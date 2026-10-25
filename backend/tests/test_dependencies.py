import json

import pytest

from backend.app.security.ingestion import read_local
from backend.app.services.assessment import assess


@pytest.mark.parametrize("filename,text,expected", [
    ("requirements.txt", "Flask==3.1.2\nrequests>=2\n", {"Flask", "requests"}),
    ("package.json", '{"dependencies":{"react":"^19.0.0"},"devDependencies":{"vite":"6.0.0"}}', {"react", "vite"}),
    ("pyproject.toml", '[project]\nname="x"\ndependencies=["flask==3.1.2"]\n[project.optional-dependencies]\ntest=["pytest>=8"]', {"flask", "pytest"}),
    ("pyproject.toml", '[tool.poetry.dependencies]\npython="^3.11"\nflask="^3.1"', {"flask"}),
    ("pom.xml", '<project xmlns="http://maven.apache.org/POM/4.0.0"><dependencies><dependency><groupId>org.example</groupId><artifactId>library</artifactId><version>1.2.0</version></dependency></dependencies></project>', {"org.example:library"}),
    ("build.gradle", "implementation 'org.example:library:1.0.0'", {"org.example:library"}),
])
def test_manifest_formats(tmp_path, filename, text, expected):
    (tmp_path / filename).write_text(text)
    result = assess(read_local(tmp_path))
    assert {d["name"] for d in result["dependencies"]} == expected
    assert all(d["vulnerability_status"] == "not checked" for d in result["dependencies"])


@pytest.mark.parametrize("filename,text", [("package.json", "not json"), ("pyproject.toml", "[broken"), ("pom.xml", "<broken>")])
def test_invalid_manifests_warn_without_crashing(tmp_path, filename, text):
    (tmp_path / filename).write_text(text)
    assert assess(read_local(tmp_path))["warnings"]


def test_dependency_url_credential_not_exported(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"pkg": "https://token:PRIVATE_TOKEN@host.invalid/pkg"}}))
    output = json.dumps(assess(read_local(tmp_path)))
    assert "PRIVATE_TOKEN" not in output
    assert "reference omitted" in output


def test_xml_entities_rejected(tmp_path):
    (tmp_path / "pom.xml").write_text('<!DOCTYPE x [<!ENTITY secret SYSTEM "file:///etc/passwd">]><project>&secret;</project>')
    result = assess(read_local(tmp_path))
    assert any(w["code"] == "xml-dtd" for w in result["warnings"])


def test_requirements_include_not_followed(tmp_path):
    (tmp_path / "requirements.txt").write_text("-r ../../private.txt")
    result = assess(read_local(tmp_path))
    assert not result["dependencies"]
    assert result["warnings"][0]["code"] == "requirements-directive"
