from fastapi.testclient import TestClient
from backend.app import workspace as w


def test_health_and_timing(tmp_path, monkeypatch):
    monkeypatch.setattr(w, "DB", tmp_path / "state.sqlite3")
    with TestClient(w.app) as client:
        r = client.get("/healthz")
        assert r.status_code == 200 and r.json()["database"] == "ready"
        assert "Server-Timing" in r.headers
