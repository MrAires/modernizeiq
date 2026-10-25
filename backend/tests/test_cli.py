import json

from backend.app.cli import main


def test_cli_writes_reports_and_requires_explicit_overwrite(tmp_path):
    repo, out = tmp_path / "repo", tmp_path / "out"
    repo.mkdir()
    (repo / "app.py").write_text("DEBUG=True")
    args = ["analyze", "--repo", str(repo), "--out", str(out)]
    assert main(args) == 0
    assert (out / "assessment.html").exists()
    assert (out / "executive-summary.txt").exists()
    assert json.loads((out / "assessment.json").read_text())["profile"]["primary_language"] == "Python"
    assert main(args) == 2
    assert main(args + ["--overwrite"]) == 0


def test_cli_refuses_output_in_input(tmp_path):
    (tmp_path / "app.py").write_text("x=1")
    assert main(["analyze", "--repo", str(tmp_path), "--out", str(tmp_path / "out")]) == 2
