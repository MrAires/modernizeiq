import json
from pathlib import Path

import pytest

from backend.app.core.models import AssessmentError
from backend.app.scoring.engine import DEFAULT_CONFIG, load_config
from backend.app.security.ingestion import read_local
from backend.app.services.assessment import assess, validate_references
from backend.app.services.report import render_html
from benchmarks.evaluate import evaluate

ROOT = Path(__file__).resolve().parents[2]


def analyze_text(tmp_path, text, name="app.py"):
    (tmp_path / name).write_text(text, encoding="utf-8")
    return assess(read_local(tmp_path))


def rules(data):
    return {f["rule_id"] for f in data["findings"]}


def test_demo_benchmark_and_control():
    result = evaluate()["results"]
    assert result["legacy-commerce"]["expected"] == 11
    for row in result.values():
        assert not row["missed"]
        assert not row["false_positives"]
    assert result["improved-control"]["readiness"] > result["legacy-commerce"]["readiness"]


def test_deterministic_output_and_references():
    inventory = read_local(ROOT / "demo-apps" / "legacy-commerce")
    first, second = assess(inventory), assess(inventory)
    assert first == second
    validate_references(first)
    files = {f.path: f for f in inventory.files}
    for evidence in first["evidence"]:
        if evidence["file"] != "<inventory>":
            assert evidence["file_sha256"] == files[evidence["file"]].sha256
            if evidence["line"]:
                assert 1 <= evidence["line"] <= len(files[evidence["file"]].text.splitlines())


def test_secret_values_never_exported(tmp_path):
    secret = "SENSITIVE_VALUE_123456"
    data = analyze_text(tmp_path, f'DATABASE_PASSWORD = "{secret}"\nPAYMENT_URL="https://user:{secret}@example.invalid/path"')
    assert "SECRET_LITERAL" in rules(data)
    assert secret not in json.dumps(data)
    assert secret not in render_html(data)


@pytest.mark.parametrize("code", [
    'import os\nPASSWORD=os.environ["PASSWORD"]',
    'import os\nPASSWORD=os.getenv("PASSWORD")',
    'PASSWORD="${PASSWORD}"',
    'PASSWORD="changeme"',
    '# PASSWORD="sensitive"\nx=1',
])
def test_secret_negative_controls(tmp_path, code):
    assert "SECRET_LITERAL" not in rules(analyze_text(tmp_path, code))


def test_ast_security_and_routes(tmp_path):
    data = analyze_text(tmp_path, '''import subprocess
cursor.execute("SELECT " + user_input)
subprocess.run(command, shell=True)
@app.post("/orders")
def create_order(): pass
''')
    assert {"SQL_CONSTRUCTION", "SHELL_ENABLED"} <= rules(data)
    assert data["profile"]["api_inventory"][0]["methods"] == ["POST"]
    assert data["profile"]["api_inventory"][0]["authentication"] == "not inferred"


def test_invalid_python_records_uncertainty(tmp_path):
    data = analyze_text(tmp_path, "def broken(:")
    assert data["warnings"][0]["code"] == "python-syntax"
    security = next(c for c in data["readiness"]["categories"] if c["category"] == "Security")
    assert all(c["status"] == "unknown" for c in security["checks"])


def test_score_recomputes_from_exported_checks():
    data = assess(read_local(ROOT / "demo-apps" / "legacy-commerce"))
    categories = data["readiness"]["categories"]
    for category in categories:
        assert category["score"] == round(100 * sum(c["points_earned"] for c in category["checks"]) / sum(c["points_possible"] for c in category["checks"]), 1)
    assert data["readiness"]["overall"] == round(sum(c["score"] * c["weight"] for c in categories) / sum(c["weight"] for c in categories), 1)


def test_configuration_change_is_visible(tmp_path):
    original = assess(read_local(ROOT / "demo-apps" / "legacy-commerce"))
    config = json.loads(DEFAULT_CONFIG.read_text())
    config["category_weights"]["Security"] = 100
    path = tmp_path / "scores.json"
    path.write_text(json.dumps(config))
    changed = assess(read_local(ROOT / "demo-apps" / "legacy-commerce"), path)
    assert changed["readiness"]["config_sha256"] != original["readiness"]["config_sha256"]
    assert changed["readiness"]["overall"] != original["readiness"]["overall"]


def test_config_rejects_bad_reference(tmp_path):
    config = json.loads(DEFAULT_CONFIG.read_text())
    config["checks"][0][-1] = "does_not_exist"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(config))
    with pytest.raises(AssessmentError):
        load_config(path)


def test_html_escapes_repository_names(tmp_path):
    data = analyze_text(tmp_path, "x=1")
    data["name"] = '<script>alert("bad")</script>'
    html = render_html(data)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "default-src 'none'" in html


def test_evidence_tampering_is_rejected(tmp_path):
    data = analyze_text(tmp_path, 'DEBUG=True')
    data["recommendations"][0]["evidence_ids"] = ["nonexistent"]
    with pytest.raises(ValueError, match="missing evidence"):
        validate_references(data)


def test_ground_truth_is_outside_input():
    inventory = read_local(ROOT / "demo-apps" / "legacy-commerce")
    assert not any("expected_findings" in file.path for file in inventory.files)


def test_python_config_subscripts_and_cors(tmp_path):
    data = analyze_text(tmp_path, '''app.config["DEBUG"] = True
app.add_middleware(CORSMiddleware, allow_origins=["*"])
''')
    assert {"DEBUG_ENABLED", "CORS_WILDCARD"} <= rules(data)


def test_properties_environment_placeholder(tmp_path):
    data = analyze_text(tmp_path, 'database.password=${DATABASE_PASSWORD}\n', "application.properties")
    assert "SECRET_LITERAL" not in rules(data)


def test_line_location_changes_with_source(tmp_path):
    original = analyze_text(tmp_path, 'DEBUG = True\n')
    changed = analyze_text(tmp_path, '# added comment\nDEBUG = True\n')
    before = next(e for e in original["evidence"] if e["rule_id"] == "DEBUG_ENABLED")
    after = next(e for e in changed["evidence"] if e["rule_id"] == "DEBUG_ENABLED")
    assert before["line"] == 1 and after["line"] == 2
    assert before["id"] != after["id"]
    assert original["snapshot_sha256"] != changed["snapshot_sha256"]
