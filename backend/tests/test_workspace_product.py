import io
import json
import zipfile
import pytest
from fastapi.testclient import TestClient
from backend.app import workspace as w


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(w, "DB", tmp_path / "product.db")
    return TestClient(w.app)


def test_demo_is_populated_idempotent_and_preserves_reviews(client):
    first = client.post("/api/demo")
    assert first.status_code == 200
    ids = first.json()["ids"]
    primary = first.json()["primary"]
    run = client.get("/api/runs/" + primary).json()
    assert run["context"]["kind"] == "demo"
    assert run["payload"]["findings"]
    finding = run["payload"]["findings"][0]["id"]
    assert (
        client.post(
            "/api/runs/" + primary + "/reviews",
            json={"item": finding, "decision": "investigate", "note": "Inspect the source window."},
        ).status_code
        == 200
    )
    assert client.post("/api/demo").json()["ids"] == ids
    assert len(client.get("/api/runs").json()) == len(ids)
    assert len(client.get("/api/runs/" + primary + "/reviews").json()) == 1
    if w.PRODUCT == "ModernizeIQ":
        control = client.get("/api/runs/demo-v3-improved").json()["payload"]
        assert control["readiness"]["overall"] > run["payload"]["readiness"]["overall"]
        assert not control["findings"]
    else:
        assert len(run["payload"]["services"]) == 6
        assert run["payload"]["profile"]["samples"] == 270
        for name in ("healthy", "transient"):
            assert not client.get("/api/runs/demo-v3-" + name).json()["payload"]["findings"]


def test_sample_roundtrip_and_human_readable_exports(client):
    sample = client.get("/api/sample")
    assert sample.status_code == 200
    if w.PRODUCT == "ModernizeIQ":
        with zipfile.ZipFile(io.BytesIO(sample.content)) as archive:
            assert "config.py" in archive.namelist()
    imported = client.post(
        "/api/import?name=Sample+roundtrip",
        content=sample.content,
        headers={"content-type": "application/zip" if w.PRODUCT == "ModernizeIQ" else "text/csv"},
    )
    assert imported.status_code == 200
    identifier = imported.json()["id"]
    report = client.get("/api/runs/" + identifier + "/report")
    assert report.status_code == 200
    assert "text/html" in report.headers["content-type"]
    assert "Sample roundtrip" in report.text
    assert "Evidence appendix" in report.text
    register = client.get("/api/runs/" + identifier + "/findings.csv")
    assert register.status_code == 200
    assert register.text.startswith("id,title,severity,category,action")


def test_report_escapes_user_text(client):
    primary = client.post("/api/demo").json()["primary"]
    run = client.get("/api/runs/" + primary).json()
    client.post(
        "/api/runs/" + primary + "/reviews",
        json={
            "item": run["payload"]["findings"][0]["id"],
            "decision": "accepted",
            "note": '<script>alert("example")</script>',
        },
    )
    html = client.get("/api/runs/" + primary + "/report").text
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_static_brand_assets_and_shell(client):
    shell = client.get("/portfolio").text
    assert "/workspace-assets/app.js" in shell
    assert "/workspace-assets/logo.svg" in shell
    assert client.get("/workspace-assets/styles.css").status_code == 200
    assert client.get("/workspace-assets/app.js").status_code == 200
    assert "<svg" in client.get("/workspace-assets/logo.svg").text
    assert client.get("/workspace-assets/missing.js").status_code == 404


def test_csv_formula_cells_are_escaped(client):
    primary = client.post("/api/demo").json()["primary"]
    run = client.get("/api/runs/" + primary).json()
    run["payload"]["findings"][0]["title"] = '=HYPERLINK("https://example.invalid")'
    with w.connection() as con:
        con.execute("UPDATE runs SET payload=? WHERE id=?", (json.dumps(run["payload"]), primary))
    csv_text = client.get("/api/runs/" + primary + "/findings.csv").text
    assert "'=HYPERLINK" in csv_text
