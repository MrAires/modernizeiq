"""Point-based heuristic with exported check-by-check calculations."""

import hashlib
import json
import math
from pathlib import Path

from backend.app.analyzers.evidence import EvidenceStore
from backend.app.core.models import AssessmentError

DEFAULT_CONFIG = Path(__file__).resolve().parents[3] / "config" / "scoring.json"
FACT_KEYS = {"layers", "migrations", "env_config", "docker", "container_health", "docker_start",
             "tests", "ci_tests", "coverage_config", "ci", "ci_container", "logging", "health",
             "telemetry", "readme", "deployment_docs", "governance_docs", "dependency_manifest", "lockfile"}
RULE_KEYS = {"LOCAL_STORAGE", "HARDCODED_URL", "SECRET_LITERAL", "DEBUG_ENABLED", "HTTP_ENDPOINT",
             "SQL_CONSTRUCTION", "SHELL_ENABLED", "CORS_WILDCARD", "DEP_UNPINNED"}


def load_config(path: Path | None = None) -> dict:
    try:
        raw = (path or DEFAULT_CONFIG).read_bytes()
        if len(raw) > 64 * 1024:
            raise ValueError
        config = json.loads(raw)
        weights = config["category_weights"]
        if not isinstance(weights, dict) or not weights:
            raise ValueError
        for key, value in weights.items():
            if not isinstance(key, str) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 < value <= 100:
                raise ValueError
        ids, used = set(), set()
        for check in config["checks"]:
            identifier, category, label, points, mode, ref = check
            if (identifier in ids or category not in weights or not isinstance(label, str)
                    or not isinstance(points, (int, float)) or not math.isfinite(points) or not 0 < points <= 100
                    or mode not in {"fact", "no_rule"} or ref not in (FACT_KEYS if mode == "fact" else RULE_KEYS)):
                raise ValueError
            ids.add(identifier)
            used.add(category)
        if used != set(weights):
            raise ValueError
        config["sha256"] = hashlib.sha256(raw).hexdigest()
        return config
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise AssessmentError("Scoring configuration is missing or invalid.") from exc


def score(store: EvidenceStore, config: dict) -> dict:
    categories = []
    for category, weight in config["category_weights"].items():
        checks = []
        for identifier, group, label, points, mode, ref in config["checks"]:
            if group != category:
                continue
            if mode == "fact":
                refs = list(store.facts.get(ref, []))
                satisfied = bool(refs)
            else:
                matches = [f for f in store.findings.values() if f["rule_id"] == ref]
                refs = [e for f in matches for e in f["evidence_ids"]]
                satisfied = not matches
            if not refs:
                refs = [store.add(identifier, None, None,
                                  "No matching indicator was observed within the inspected snapshot; unsupported or skipped files are outside this check.")]
            # A failed parser makes absence-based credit unsafe. Preserve the uncertainty.
            uncertain = mode == "no_rule" and bool(store.warnings) and satisfied
            earned = points if satisfied and not uncertain else 0
            checks.append({"id": identifier, "label": label, "points_possible": points,
                           "points_earned": earned, "status": "unknown" if uncertain else "satisfied" if satisfied else "not_satisfied",
                           "evidence_ids": sorted(set(refs)), "condition": {"mode": mode, "reference": ref}})
        earned = sum(c["points_earned"] for c in checks)
        possible = sum(c["points_possible"] for c in checks)
        categories.append({"category": category, "weight": weight, "score": round(earned / possible * 100, 1),
                           "earned": earned, "possible": possible, "checks": checks,
                           "evidence_count": len({e for c in checks for e in c["evidence_ids"]})})
    overall = round(sum(c["score"] * c["weight"] for c in categories) / sum(c["weight"] for c in categories), 1)
    return {"overall": overall, "categories": categories, "config_version": config.get("version", "unspecified"),
            "config_sha256": config["sha256"], "formula": "100 × earned check points / possible check points; overall = weighted mean of category scores",
            "interpretation": "Configurable modernization-readiness heuristic. Not a security certification, migration prediction or measured test coverage."}
