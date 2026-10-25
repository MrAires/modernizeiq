"""Demonstrations and human-readable exports for the local product workspace."""

import csv
import io
import json
import math
import zipfile
from contextlib import closing
from datetime import datetime, timedelta, timezone
from html import escape
from fastapi.responses import Response, HTMLResponse


def demo_metrics(scenario):
    rows = []
    services = [
        "api-gateway",
        "checkout-service",
        "payment-service",
        "inventory-service",
        "auth-service",
        "notification-service",
    ]
    start = datetime(2026, 10, 24, 9, 0, tzinfo=timezone.utc)
    for minute in range(45):
        for index, service in enumerate(services):
            base = 65 + index * 17 + 11 * math.sin(minute * 0.4 + index)
            bad = scenario != "healthy" and 15 <= minute <= 35 and service in {"checkout-service", "payment-service"}
            spike = scenario == "transient" and minute in {16, 24} and service == "payment-service"
            if scenario == "transient":
                bad = False
            latency = (1250 + (minute - 15) * 32 + 90 * math.sin(minute)) if bad else (1900 if spike else base)
            rate = min(0.22, 0.065 + (minute - 15) * 0.006) if bad else (0.14 if spike else 0.002 + index * 0.0005)
            rows.append(
                {
                    "timestamp": (start + timedelta(minutes=minute)).isoformat(),
                    "service_id": service,
                    "latency_p95_ms": round(latency, 2),
                    "error_rate": round(rate, 4),
                }
            )
    return rows


def install_features(app, product, root, connection, fetch, analyze_metrics):
    modern = product == "ModernizeIQ"

    @app.post("/api/demo")
    def create_demo():
        """Idempotent inserts preserve user data and previously recorded reviews."""
        variants = (
            [("legacy", "Northstar Commerce · baseline"), ("improved", "Northstar Commerce · improved control")]
            if modern
            else [
                ("incident", "Commerce checkout · sustained incident"),
                ("healthy", "Commerce checkout · healthy control"),
                ("transient", "Commerce checkout · transient spikes"),
            ]
        )
        created = []
        for index, (scenario, name) in enumerate(variants):
            identifier = "demo-v3-" + scenario
            with closing(connection()) as con:
                exists = con.execute("SELECT 1 FROM runs WHERE id=?", (identifier,)).fetchone()
            if exists:
                created.append(identifier)
                continue
            if modern:
                from backend.app.security.ingestion import read_local
                from backend.app.services.assessment import assess

                folder = "legacy-commerce" if scenario == "legacy" else "improved-control"
                data = assess(read_local(root / "demo-apps" / folder))
                data["name"] = name
            else:
                data = analyze_metrics(json.dumps(demo_metrics(scenario)), "json", 1000, 0.05, 3, 120)
            context = {
                "kind": "demo",
                "criticality": "high",
                "objective": "Compare evidence and priorities before a cloud modernization decision."
                if modern
                else "Investigate sustained checkout degradation and distinguish it from transient spikes.",
                "scenario": scenario,
                "scope": "Labelled educational demo; not production customer data",
            }
            timestamp = (datetime(2026, 10, 24, 10, 30, tzinfo=timezone.utc) - timedelta(minutes=index * 5)).isoformat()
            with closing(connection()) as con, con:
                con.execute(
                    "INSERT OR IGNORE INTO runs VALUES(?,?,?,?,?)",
                    (identifier, name, timestamp, json.dumps(context), json.dumps(data)),
                )
            created.append(identifier)
        return {
            "ids": created,
            "primary": created[0],
            "notice": "Demo data is labelled and stored separately from your imports.",
        }

    @app.get("/api/sample")
    def sample():
        buffer = io.BytesIO()
        if modern:
            fixture = root / "demo-apps" / "legacy-commerce"
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(fixture.rglob("*")):
                    if path.is_file() and "__pycache__" not in path.parts:
                        archive.write(path, path.relative_to(fixture))
            return Response(
                buffer.getvalue(),
                media_type="application/zip",
                headers={"Content-Disposition": 'attachment; filename="legacy-commerce.zip"'},
            )
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=["timestamp", "service_id", "latency_p95_ms", "error_rate"])
        writer.writeheader()
        writer.writerows(demo_metrics("incident"))
        return Response(
            out.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="commerce-telemetry.csv"'},
        )

    @app.get("/api/runs/{identifier}/findings.csv")
    def csv_export(identifier: str):
        run = fetch(identifier)
        out = io.StringIO()
        keys = ["id", "title", "severity", "category", "action"]
        writer = csv.DictWriter(out, fieldnames=keys)
        writer.writeheader()
        for finding in run["payload"].get("findings", []):
            # Protect spreadsheet users from formula injection in imported metadata.
            values = {}
            for key in keys:
                value = str(finding.get(key, ""))
                values[key] = "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value
            writer.writerow(values)
        return Response(
            out.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="findings.csv"'},
        )

    @app.get("/api/runs/{identifier}/report")
    def report(identifier: str):
        run = fetch(identifier)
        data, context = run["payload"], run["context"]
        with closing(connection()) as con:
            decisions = [
                dict(row) for row in con.execute("SELECT * FROM reviews WHERE run_id=? ORDER BY id DESC", (identifier,))
            ]

        def h(value):
            return escape(str(value), quote=True)

        findings = "".join(
            "<tr><td>"
            + h(f["severity"])
            + "</td><td><strong>"
            + h(f["title"])
            + "</strong><p>"
            + h(f.get("action", ""))
            + "</p></td><td>"
            + h(", ".join(f.get("evidence_ids", [])))
            + "</td></tr>"
            for f in data.get("findings", [])
        )
        reviews = "".join(
            "<li><strong>"
            + h(r["decision"])
            + "</strong> · "
            + h(r["item"])
            + "<p>"
            + h(r["note"])
            + "</p><small>"
            + h(r["created"])
            + "</small></li>"
            for r in decisions
        )
        scores = "".join(
            "<tr><td>" + h(c["category"]) + "</td><td>" + h(c["score"]) + " / 100</td></tr>"
            for c in data.get("readiness", {}).get("categories", [])
        )
        parameters = data.get(
            "parameters",
            {
                "config_sha256": data.get("readiness", {}).get("config_sha256"),
                "snapshot_sha256": data.get("snapshot_sha256"),
            },
        )
        evidence = "".join(
            "<details><summary>"
            + h(e["id"])
            + " · "
            + h(e.get("file", e.get("service", "Inventory")))
            + "</summary><pre>"
            + h(json.dumps(e, indent=2))
            + "</pre></details>"
            for e in data.get("evidence", [])
        )
        body = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{h(product)} report</title><style>
        body{{font:15px/1.7 system-ui;color:#222;background:#faf8f4;max-width:980px;margin:40px auto;padding:30px}}h1{{font:40px Georgia}}h2{{margin-top:36px}}table{{width:100%;border-collapse:collapse}}td,th{{padding:12px;border-bottom:1px solid #ddd;text-align:left}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#eee;padding:15px;font-size:12px}}small{{color:#666}}details{{padding:12px;border:1px solid #ddd;margin:8px 0}}button{{padding:12px 24px;background:#333;color:white;border:0;cursor:pointer}}@media print{{button{{display:none}}body{{margin:0;padding:0;background:white}}details{{break-inside:avoid}}}}
        </style><button onclick="window.print()">Print / save PDF</button><p>{h(product)} / Assessment report</p><h1>{h(run["name"])}</h1><small>{h(run["created"])} · {"Educational demo" if context.get("kind") == "demo" else "User import"}</small><h2>Purpose and scope</h2><p>{h(context.get("objective") or "No objective supplied")}</p><p>Business criticality: {h(context.get("criticality", "medium"))}. {len(data.get("findings", []))} selected findings.</p><h2>Assessment summary</h2><pre>{h(json.dumps(data.get("profile", {}), indent=2))}</pre><table>{scores}</table><h2>Priorities and findings</h2><table><tr><th>Severity</th><th>Finding and action</th><th>Evidence</th></tr>{findings or '<tr><td colspan="3">No matching findings in this scope.</td></tr>'}</table><h2>Review history</h2><ul>{reviews or "<li>No review decisions recorded.</li>"}</ul><h2>Reproducibility</h2><pre>{h(json.dumps(parameters, indent=2))}</pre><h2>Evidence appendix</h2>{evidence}<h2>Limitations</h2><ul>{"".join("<li>" + h(item) + "</li>" for item in data.get("limitations", []))}</ul><p>Review decisions record human judgment; they do not execute remediation.</p></html>"""
        return HTMLResponse(body)
