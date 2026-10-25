import io
import json
import zipfile
import pytest
from fastapi.testclient import TestClient
from backend.app import workspace as w


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(w, "DB", tmp_path / "workspace.db")
    return TestClient(w.app)


def telemetry():
    return [
        {
            "timestamp": f"2026-10-24T10:0{i}:00Z",
            "service_id": "custom-inventory",
            "latency_p95_ms": 1500,
            "error_rate": 0.1,
        }
        for i in range(3)
    ]


def upload(client):
    if w.PRODUCT == "ModernizeIQ":
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as z:
            z.writestr("app.py", "DEBUG=True\n")
        raw = stream.getvalue()
    else:
        raw = json.dumps(telemetry()).encode()
    return client.post("/api/import?name=User+project&objective=Reduce+risk", content=raw)


def test_import_persists_and_review_export(client):
    response = upload(client)
    assert response.status_code == 200, response.text
    identifier = response.json()["id"]
    run = client.get("/api/runs/" + identifier).json()
    assert run["name"] == "User project"
    assert run["context"]["objective"] == "Reduce risk"
    finding = run["payload"]["findings"][0]["id"]
    assert (
        client.post(
            "/api/runs/" + identifier + "/reviews",
            json={"item": finding, "decision": "accepted", "note": "Verified against input"},
        ).status_code
        == 200
    )
    assert len(client.get("/api/runs/" + identifier + "/export").json()["reviews"]) == 1
    assert len(client.get("/api/runs").json()) == 1
    assert (
        client.post(
            "/api/runs/" + identifier + "/reviews", json={"item": "invented", "decision": "accepted", "note": "bad"}
        ).status_code
        == 422
    )


def test_bad_input_and_cross_origin(client):
    assert client.post("/api/import", content=b"invalid").status_code == 422
    assert (
        client.post("/api/import", content=b"invalid", headers={"origin": "https://unrelated.example"}).status_code
        == 403
    )
    assert client.get("/api/runs/missing").status_code == 404
    assert client.get("/missing-page").status_code == 404


def test_all_pages(client):
    for page in w.PAGES:
        assert client.get("/" + page.lower()).status_code == 200


def test_generic_detector_parameters_and_gaps():
    raw = json.dumps(telemetry()).encode()
    data = w.analyze_metrics(raw, "json", 1000, 0.05, 3, 120)
    assert len(data["findings"]) == 1
    assert "custom-inventory" in data["services"]
    assert not w.analyze_metrics(raw, "json", 2000, 0.05, 3, 120)["findings"]
    assert not w.analyze_metrics(raw, "json", 1000, 0.05, 3, 30)["findings"]
    rows = telemetry()
    rows[0]["error_rate"] = float("nan")
    with pytest.raises(ValueError):
        w.analyze_metrics(json.dumps(rows), "json", 1000, 0.05, 3, 120)
    rows = telemetry()
    rows.append(rows[0])
    with pytest.raises(ValueError):
        w.analyze_metrics(json.dumps(rows), "json", 1000, 0.05, 3, 120)


def test_csv_and_unsorted_records():
    raw = b"timestamp,service_id,latency_p95_ms,error_rate\n2026-10-24T10:02:00Z,new,1300,0.1\n2026-10-24T10:00:00Z,new,1400,0.2\n2026-10-24T10:01:00Z,new,1500,0.3\n"
    assert len(w.analyze_metrics(raw, "csv", 1000, 0.05, 3, 120)["findings"]) == 1
