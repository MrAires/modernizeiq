"""Local research workspace. Run with uvicorn backend.app.workspace:app."""

import logging
import time
import csv
import io
import json
import math
import os
import sqlite3
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from contextlib import closing
from pydantic import BaseModel, Field
from backend.app.workspace_features import install_features
from backend.app.core.models import AssessmentError

PRODUCT = "ModernizeIQ"
ROOT = Path(__file__).resolve().parents[2]
DB = Path(os.environ.get("WORKSPACE_DB", str(ROOT / "data" / "workspace.sqlite3")))
app = FastAPI(title=PRODUCT + " Studio", version="3.0")


def connection():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.executescript("""CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,name TEXT,created TEXT,context TEXT,payload TEXT);
    CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY,run_id TEXT,item TEXT,decision TEXT,note TEXT,created TEXT);""")
    return con


@app.middleware("http")
async def local_boundary(request: Request, call_next):
    host = request.headers.get("host", "").split(":")[0]
    if host not in {"127.0.0.1", "localhost", "testserver"}:
        return Response("Local workspace only", status_code=403)
    origin = request.headers.get("origin")
    if request.method != "GET" and origin and origin != str(request.base_url).rstrip("/"):
        return Response("Cross-origin writes rejected", status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


def fetch(identifier):
    with closing(connection()) as con, con:
        row = con.execute("SELECT * FROM runs WHERE id=?", (identifier,)).fetchone()
    if not row:
        raise HTTPException(404, "Assessment not found")
    result = dict(row)
    result["payload"] = json.loads(result["payload"])
    result["context"] = json.loads(result["context"])
    return result


@app.get("/api/runs")
def runs():
    with closing(connection()) as con, con:
        result = []
        for row in con.execute("SELECT * FROM runs ORDER BY created DESC LIMIT 200"):
            data, context = json.loads(row["payload"]), json.loads(row["context"])
            result.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "created": row["created"],
                    "context": context,
                    "findings": len(data.get("findings", [])),
                    "score": data.get("readiness", {}).get("overall"),
                    "profile": data.get("profile", {}),
                    "high": sum(f.get("severity") == "high" for f in data.get("findings", [])),
                }
            )
        return result


@app.get("/api/runs/{identifier}")
def detail(identifier: str):
    return fetch(identifier)


@app.get("/api/runs/{identifier}/export")
def export(identifier: str):
    result = fetch(identifier)
    with closing(connection()) as con, con:
        result["reviews"] = [
            dict(r) for r in con.execute("SELECT * FROM reviews WHERE run_id=? ORDER BY id", (identifier,))
        ]
    return Response(
        json.dumps(result, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="assessment.json"'},
    )


class Review(BaseModel):
    item: str = Field(min_length=1, max_length=160)
    decision: str
    note: str = Field(min_length=1, max_length=2000)


@app.post("/api/runs/{identifier}/reviews")
def review(identifier: str, body: Review):
    run = fetch(identifier)
    if body.decision not in {"accepted", "rejected", "deferred", "investigate"}:
        raise HTTPException(422, "Unsupported decision")
    if body.item not in {f["id"] for f in run["payload"]["findings"]}:
        raise HTTPException(422, "Finding is not part of this assessment")
    with closing(connection()) as con, con:
        con.execute(
            "INSERT INTO reviews(run_id,item,decision,note,created) VALUES(?,?,?,?,?)",
            (identifier, body.item, body.decision, body.note, datetime.now(timezone.utc).isoformat()),
        )
    return {"status": "recorded", "effect": "Review only; no infrastructure or source code changed"}


@app.get("/api/runs/{identifier}/reviews")
def reviews(identifier: str):
    fetch(identifier)
    with closing(connection()) as con, con:
        return [dict(r) for r in con.execute("SELECT * FROM reviews WHERE run_id=? ORDER BY id DESC", (identifier,))]


def analyze_metrics(raw, suffix, latency, error, samples, gap):
    """Generic sustained multi-signal detector; causal claims remain unproven."""
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))) if suffix == "csv" else json.loads(raw)
    if isinstance(rows, dict):
        rows = rows.get("metrics", [])
    if not isinstance(rows, list) or not 1 <= len(rows) <= 50000:
        raise ValueError("Provide 1–50,000 metric records")
    groups = {}
    seen = set()
    for row in rows:
        service = str(row["service_id"]).strip()
        if not service or len(service) > 120:
            raise ValueError("Invalid service_id")
        timestamp = datetime.fromisoformat(str(row["timestamp"]).replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError("Timestamps require timezone offsets or Z")
        timestamp = timestamp.astimezone(timezone.utc)
        key = (service, timestamp)
        if key in seen:
            raise ValueError("Duplicate service/timestamp record")
        seen.add(key)
        p95, rate = float(row["latency_p95_ms"]), float(row["error_rate"])
        if not math.isfinite(p95) or not math.isfinite(rate) or p95 < 0 or not 0 <= rate <= 1:
            raise ValueError("Latency must be finite and nonnegative; error_rate must be a fraction 0–1")
        groups.setdefault(service, []).append(
            {"timestamp": timestamp.isoformat(), "latency_p95_ms": p95, "error_rate": rate}
        )
    findings, evidence = [], []
    for service, points in sorted(groups.items()):
        points.sort(key=lambda p: p["timestamp"])
        streak = []
        for p in points:
            if (
                streak
                and (
                    datetime.fromisoformat(p["timestamp"]) - datetime.fromisoformat(streak[-1]["timestamp"])
                ).total_seconds()
                > gap
            ):
                streak = []
            if p["latency_p95_ms"] >= latency and p["error_rate"] >= error:
                streak.append(p)
            else:
                streak = []
            if len(streak) == samples:
                ref = "evidence-" + str(len(evidence) + 1)
                evidence.append(
                    {
                        "id": ref,
                        "service": service,
                        "observations": streak.copy(),
                        "description": "Both latency and error thresholds exceeded in consecutive samples. This does not establish a root cause.",
                    }
                )
                findings.append(
                    {
                        "id": "incident-" + str(len(findings) + 1),
                        "title": service + ": sustained latency and errors",
                        "severity": "high",
                        "category": "Reliability",
                        "evidence_ids": [ref],
                        "action": "Inspect this time window in deployment logs and traces. Validate downstream dependencies before choosing remediation.",
                    }
                )
    return {
        "findings": findings,
        "evidence": evidence,
        "services": groups,
        "profile": {"services": len(groups), "samples": len(rows)},
        "parameters": {
            "latency_ms": latency,
            "error_rate": error,
            "consecutive_samples": samples,
            "maximum_gap_seconds": gap,
        },
        "limitations": [
            "Metric-only import does not establish causation. No automated remediation.",
            "No incidents means no matching multi-signal window under these settings, not proof of health.",
        ],
    }


@app.post("/api/import")
async def ingest(
    request: Request,
    name: str = "Untitled",
    criticality: str = "medium",
    objective: str = "",
    latency: float = 1000,
    error: float = 0.05,
    samples: int = 3,
    gap: int = 120,
):
    if not 1 <= len(name.strip()) <= 120 or len(objective) > 1000 or criticality not in {"low", "medium", "high"}:
        raise HTTPException(422, "Invalid name or business context")
    if (
        not math.isfinite(latency)
        or latency <= 0
        or not math.isfinite(error)
        or not 0 < error <= 1
        or not 2 <= samples <= 100
        or not 1 <= gap <= 86400
    ):
        raise HTTPException(422, "Invalid detector settings")
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 10 * 1024 * 1024:
            raise HTTPException(413, "Upload exceeds 10 MiB")
    try:
        if PRODUCT == "ModernizeIQ":
            from backend.app.security.ingestion import read_zip
            from backend.app.services.assessment import assess

            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "repository.zip"
                path.write_bytes(raw)
                data = assess(read_zip(path))
            data["name"] = name.strip()
        else:
            data = analyze_metrics(
                raw, "csv" if "csv" in request.headers.get("content-type", "") else "json", latency, error, samples, gap
            )
    except AssessmentError as exc:
        raise HTTPException(422, str(exc)) from exc
    except (ValueError, KeyError, TypeError, UnicodeError, OSError) as exc:
        raise HTTPException(
            422,
            "Input could not be assessed. Check format, field types, timezone timestamps and supported archive limits.",
        ) from exc
    identifier = uuid.uuid4().hex
    context = {"criticality": criticality, "objective": objective, "scope": "local single-user research workspace"}
    with closing(connection()) as con, con:
        con.execute(
            "INSERT INTO runs VALUES(?,?,?,?,?)",
            (identifier, name.strip(), datetime.now(timezone.utc).isoformat(), json.dumps(context), json.dumps(data)),
        )
    return {"id": identifier}


# Add routes before the HTML catch-all.
install_features(app, PRODUCT, ROOT, connection, fetch, analyze_metrics)

PAGES = [
    "Portfolio",
    "Import",
    "Assessment",
    "Evidence",
    "Review",
    "Compare",
    "Reports",
    "Audit",
    "Guide",
    "Services",
    "Signals",
    "Findings",
    "Architecture",
    "Dependencies",
    "Roadmap",
]
WEB = ROOT / "workspace_ui"
app.mount("/workspace-assets", StaticFiles(directory=WEB), name="workspace-assets")


@app.get("/healthz")
def healthz():
    with closing(connection()) as con:
        result = con.execute("PRAGMA quick_check").fetchone()[0]
    if result != "ok":
        raise HTTPException(503, "Database integrity check failed")
    return {"status": "ok", "database": "ready"}


@app.middleware("http")
async def request_metrics(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["Server-Timing"] = f"app;dur={(time.perf_counter() - started) * 1000:.2f}"
    logging.getLogger("workspace").info("%s %s %s", request.method, request.url.path, response.status_code)
    return response


@app.get("/{page:path}", response_class=HTMLResponse)
def ui(page: str):
    if page and page not in [p.lower() for p in PAGES]:
        raise HTTPException(404, "Page not found")
    return (
        (WEB / "index.html")
        .read_text(encoding="utf-8")
        .replace("__PRODUCT__", PRODUCT)
        .replace("__MODE__", "modern" if PRODUCT == "ModernizeIQ" else "ops")
    )
