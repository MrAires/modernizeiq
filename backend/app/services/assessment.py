"""The orchestration boundary: ingestion is separate from this pure assessment."""

from dataclasses import asdict
from pathlib import Path

from backend.app import VERSION
from backend.app.analyzers.dependencies import parse_dependencies
from backend.app.analyzers.evidence import EvidenceStore
from backend.app.analyzers.inspection import inspect
from backend.app.core.models import Inventory, Limits
from backend.app.recommendations.planner import add_missing_indicators, plan
from backend.app.scoring.engine import load_config, score


def infer_architecture(profile: dict, store: EvidenceStore) -> dict:
    refs = sorted(set(store.facts.get("framework", []) + store.facts.get("api_route", [])))
    nodes = [{"id": "application", "label": "Application source", "kind": "application", "evidence_ids": refs}]
    edges = []
    db_refs = sorted(
        set(store.facts.get("db_sqlite", []) + store.facts.get("db_relational", []) + store.facts.get("db_import", []))
    )
    if profile["databases"]:
        nodes.append(
            {"id": "database", "label": ", ".join(profile["databases"]), "kind": "database", "evidence_ids": db_refs}
        )
        edges.append(
            {"from": "application", "to": "database", "relation": "database use inferred", "evidence_ids": db_refs}
        )
    local = [e for f in store.findings.values() if f["rule_id"] == "LOCAL_STORAGE" for e in f["evidence_ids"]]
    if local:
        nodes.append({"id": "storage", "label": "Local persistence", "kind": "storage", "evidence_ids": local})
        edges.append(
            {"from": "application", "to": "storage", "relation": "local state inferred", "evidence_ids": local}
        )
    endpoints = [e for f in store.findings.values() if f["rule_id"] == "HARDCODED_URL" for e in f["evidence_ids"]]
    if endpoints:
        nodes.append(
            {"id": "external", "label": "Configured endpoint(s)", "kind": "external", "evidence_ids": endpoints}
        )
        edges.append(
            {
                "from": "application",
                "to": "external",
                "relation": "endpoint reference; call not proven",
                "evidence_ids": endpoints,
            }
        )
    return {
        "style": "Single-application / monolith candidate" if refs else "Insufficient evidence to classify",
        "confidence": "low — static hypothesis",
        "nodes": nodes,
        "edges": edges,
        "caution": "This is an inferred dependency sketch, not a runtime call graph or proof of deployment boundaries.",
        "strategy": "Preserve a simple deployment model while validating module boundaries. Microservices require independent scale, ownership or release needs not established by this scan.",
    }


def assess(inventory: Inventory, config_path: Path | None = None) -> dict:
    # Demo sources are separate applications, not evidence about their host repository.
    excluded = [f for f in inventory.files if set(Path(f.path).parts[:-1]) & {"demo-apps", "examples", "samples"}]
    if excluded:
        from backend.app.security.ingestion import inventory as make_inventory

        inventory = make_inventory(
            inventory.name,
            inventory.source_kind,
            [f for f in inventory.files if f not in excluded],
            list(inventory.skipped)
            + [{"path": f.path, "reason": "demonstration source excluded from application scope"} for f in excluded],
        )
    store = EvidenceStore()
    dependencies = parse_dependencies(inventory.files, store)
    profile = inspect(inventory, dependencies, store)
    if profile["primary_language"] == "Unknown":
        store.warn(
            inventory.files[0],
            "source-scope",
            "No recognized source language was observed; structural and absence-based checks are incomplete.",
        )
    add_missing_indicators(store, profile)
    architecture = infer_architecture(profile, store)
    readiness = score(store, load_config(config_path))
    recommendations = plan(store)
    assessment = {
        "schema_version": "1.0",
        "analyzer_version": VERSION,
        "name": inventory.name,
        "source_kind": inventory.source_kind,
        "snapshot_sha256": inventory.fingerprint,
        "profile": profile,
        "dependencies": dependencies,
        "architecture": architecture,
        "readiness": readiness,
        "findings": sorted(store.findings.values(), key=lambda f: (f["rule_id"], f["id"])),
        "recommendations": recommendations,
        "evidence": sorted(store.evidence.values(), key=lambda e: e["id"]),
        "files": [{"path": f.path, "bytes": f.size, "sha256": f.sha256} for f in inventory.files],
        "skipped": list(inventory.skipped),
        "warnings": store.warnings,
        "status": "limited" if inventory.skipped or store.warnings else "assessed within supported scope",
        "limits": asdict(Limits()),
        "limitations": [
            "Static patterns can miss findings or produce false positives.",
            "No repository code, tests, builds, dependency installs or external services were executed.",
            "Dependency vulnerability, age and deprecation were not checked.",
            "Scores are configurable heuristics; missing observations are not runtime proof.",
            "Deterministic analysis; no LLM reasoning. The Studio provides API and database history.",
            "Bundled demo-apps, examples and samples are excluded from application assessment. A high score is not proof of security.",
        ],
    }
    validate_references(assessment)
    return assessment


def validate_references(assessment: dict) -> None:
    """Reject internal mistakes rather than publishing untraceable recommendations."""
    evidence = {e["id"] for e in assessment["evidence"]}
    findings = {f["id"] for f in assessment["findings"]}
    recommendations = {r["id"] for r in assessment["recommendations"]}
    items = assessment["findings"] + assessment["recommendations"] + assessment["dependencies"]
    items += [c for category in assessment["readiness"]["categories"] for c in category["checks"]]
    items += assessment["architecture"]["nodes"] + assessment["architecture"]["edges"]
    for item in items:
        if not set(item["evidence_ids"]) <= evidence:
            raise ValueError("An assessment item refers to missing evidence.")
    for rec in assessment["recommendations"]:
        if not rec["finding_ids"] or not set(rec["finding_ids"]) <= findings:
            raise ValueError("A recommendation lacks supporting findings.")
        if not set(rec["depends_on"]) <= recommendations:
            raise ValueError("A recommendation has an invalid prerequisite.")
