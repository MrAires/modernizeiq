"""Offline evaluation: ground truth is read only here, after assessment."""

import json
from pathlib import Path

from backend.app.security.ingestion import read_local
from backend.app.services.assessment import assess

ROOT = Path(__file__).resolve().parents[1]


def evaluate() -> dict:
    truth = json.loads((ROOT / "benchmarks" / "expected_findings.json").read_text())
    results = {}
    for name in ("legacy-commerce", "improved-control"):
        result = assess(read_local(ROOT / "demo-apps" / name))
        evidence = {e["id"]: e for e in result["evidence"]}
        actual = {(f["rule_id"], evidence[f["evidence_ids"][0]]["file"], evidence[f["evidence_ids"][0]]["line"]) for f in result["findings"]}
        expected = {tuple(row) for row in truth[name]}
        true_positives = actual & expected
        actual_categories = {f["rule_id"]: f["category"] for f in result["findings"]}
        categories = {}
        for category in sorted(set(truth["rule_categories"].values()) | set(actual_categories.values())):
            want = {row for row in expected if truth["rule_categories"].get(row[0]) == category}
            found = {row for row in actual if actual_categories.get(row[0]) == category}
            matched = len(want & found)
            categories[category] = {"expected": len(want), "detected": len(found), "matched": matched,
                                    "precision": matched / len(found) if found else None,
                                    "recall": matched / len(want) if want else None}
        results[name] = {"expected": len(expected), "detected": len(actual), "matched": len(true_positives),
                         "missed": sorted(expected - actual, key=str), "false_positives": sorted(actual - expected, key=str),
                         "precision": len(true_positives) / len(actual) if actual else None,
                         "recall": len(true_positives) / len(expected) if expected else None,
                         "readiness": result["readiness"]["overall"], "categories": categories}
    return {"scope": "Two controlled educational fixtures only; not a real-world accuracy estimate.", "results": results}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
