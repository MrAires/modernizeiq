"""A small rule planner. Proposed actions require human confirmation."""

from backend.app.analyzers.evidence import EvidenceStore

PHASES = ["Stabilize", "Prepare", "Automate", "Modernize"]
PRIORITY = {"high": "P0", "medium": "P1", "low": "P2"}
MISSING = [
    ("docker", "MISSING_DOCKER", "Containerization", "medium", "Container recipe not observed",
     "No Dockerfile was found within the inspected scope.", "After configuration/state review, add and test a container recipe.", "Prepare", "Medium"),
    ("tests", "MISSING_TESTS", "Testing", "high", "Test files not observed",
     "No supported test-named files were found; this is not a coverage measurement.", "Add behavior tests around critical workflows before refactoring.", "Stabilize", "Medium"),
    ("ci", "MISSING_CI", "CI/CD", "medium", "CI configuration not observed",
     "No recognized CI definition was found within the inspected scope.", "Automate tests and checks in CI, then validate a run before enabling releases.", "Automate", "Medium"),
    ("logging", "MISSING_LOGGING", "Observability", "low", "Logging import not observed",
     "No supported Python logging import was found; other languages or wrappers may be missed.", "Review runtime logging and add structured request/error context where absent.", "Prepare", "Low"),
    ("health", "MISSING_HEALTH", "Operational Readiness", "medium", "Health route not observed",
     "No supported conventional health route was found; suitability depends on application type.", "For a long-running service, add meaningful liveness/readiness checks; mark not applicable for a library or batch job.", "Prepare", "Low"),
]


def add_missing_indicators(store: EvidenceStore, profile: dict) -> None:
    for key, rule, category, severity, title, why, action, phase, effort in MISSING:
        # Service-only readiness recommendations are not appropriate for every repository.
        if key == "health" and not profile["frameworks"]:
            continue
        if key == "logging" and profile["primary_language"] != "Python":
            continue
        if not store.facts.get(key):
            store.finding(rule, None, None, category, severity, title, why, action, phase, effort, "scope-limited absence")


def plan(store: EvidenceStore) -> list[dict]:
    grouped: dict[str, dict] = {}
    for finding in store.findings.values():
        rule = finding["rule_id"]
        if rule not in grouped:
            grouped[rule] = {"id": "rec-" + rule.lower(), "rule_id": rule, "title": finding["action"],
                             "priority": PRIORITY[finding["severity"]], "phase": finding["phase"],
                             "effort": finding["effort"], "impact": "High" if finding["severity"] == "high" else "Medium" if finding["severity"] == "medium" else "Low",
                             "status": "proposed — human review required", "finding_ids": [], "evidence_ids": [],
                             "depends_on": []}
        item = grouped[rule]
        item["finding_ids"].append(finding["id"])
        item["evidence_ids"].extend(finding["evidence_ids"])
    for rule, item in grouped.items():
        item["evidence_ids"] = sorted(set(item["evidence_ids"]))
        if rule == "MISSING_DOCKER":
            item["depends_on"] = [grouped[key]["id"] for key in ("SECRET_LITERAL", "HARDCODED_URL", "LOCAL_STORAGE") if key in grouped]
        if rule == "MISSING_CI" and "MISSING_TESTS" in grouped:
            item["depends_on"] = [grouped["MISSING_TESTS"]["id"]]
    return sorted(grouped.values(), key=lambda item: (PHASES.index(item["phase"]), item["priority"], item["id"]))
