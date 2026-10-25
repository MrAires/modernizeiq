import zipfile
import pytest
from backend.app.security.ingestion import read_zip
from backend.app.services.assessment import assess
from backend.app.core.models import AssessmentError
from fastapi.testclient import TestClient
from backend.app import workspace as w


def test_ignored_large_bundle_does_not_block_source(tmp_path):
    p = tmp_path / "repo.zip"
    with zipfile.ZipFile(p, "w", zipfile.ZIP_STORED) as z:
        z.writestr("repo/frontend/dist/app.js.map", "x" * 600000)
        z.writestr("repo/app.py", 'print("hello")')
    inventory = read_zip(p)
    assert len(inventory.files) == 1


def test_large_supported_file_still_rejected(tmp_path):
    p = tmp_path / "repo.zip"
    with zipfile.ZipFile(p, "w", zipfile.ZIP_STORED) as z:
        z.writestr("app.py", "x" * 600000)
    with pytest.raises(AssessmentError):
        read_zip(p)


def test_demo_framework_does_not_contaminate_host(tmp_path):
    p = tmp_path / "repo.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("app.py", "from fastapi import FastAPI\napp=FastAPI()")
        z.writestr("demo-apps/weak/app.py", "from flask import Flask\nDEBUG=True")
    a = assess(read_zip(p))
    assert a["profile"]["frameworks"] == ["FastAPI"]
    assert not any(f["rule_id"] == "DEBUG_ENABLED" for f in a["findings"])


def test_error_reason_visible(tmp_path, monkeypatch):
    monkeypatch.setattr(w, "DB", tmp_path / "db")
    with TestClient(w.app) as c:
        r = c.post("/api/import?name=bad", content=b"not zip")
        assert r.status_code == 422
        assert "ZIP" in r.json()["detail"]
