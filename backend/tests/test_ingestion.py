from pathlib import Path
import stat
import zipfile

import pytest

from backend.app.core.models import AssessmentError, Limits
from backend.app.security.ingestion import read_local, read_zip


def make_zip(tmp_path: Path, items: list[tuple], compression=zipfile.ZIP_STORED) -> Path:
    path = tmp_path / "sample.zip"
    with zipfile.ZipFile(path, "w", compression=compression) as z:
        for name, text in items:
            z.writestr(name, text)
    return path


def test_local_inventory_and_exclusions(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "bad.py").write_text("do_not_read = True")
    (tmp_path / "image.png").write_bytes(b"abc")
    result = read_local(tmp_path)
    assert [f.path for f in result.files] == ["app.py"]
    assert len(result.skipped) == 2


@pytest.mark.parametrize("name", ["../app.py", "/app.py", "C:/app.py", "a/../../app.py", "a\\..\\app.py", "file.py:stream", "a//app.py"])
def test_zip_rejects_unsafe_names(tmp_path, name):
    with pytest.raises(AssessmentError):
        read_zip(make_zip(tmp_path, [(name, "x=1")]))


def test_zip_rejects_symlink(tmp_path):
    info = zipfile.ZipInfo("link.py")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with pytest.raises(AssessmentError, match="links"):
        read_zip(make_zip(tmp_path, [(info, "outside.py")]))


def test_zip_case_collision(tmp_path):
    with pytest.raises(AssessmentError, match="case-colliding"):
        read_zip(make_zip(tmp_path, [("APP.py", "x=1"), ("app.py", "x=2")]))


def test_zip_ratio_limit(tmp_path):
    with pytest.raises(AssessmentError, match="compression"):
        read_zip(make_zip(tmp_path, [("app.py", "x" * 100000)], zipfile.ZIP_DEFLATED))


def test_zip_entry_limit(tmp_path):
    path = make_zip(tmp_path, [("a.py", "a=1"), ("b.py", "b=2")])
    with pytest.raises(AssessmentError, match="entry limit"):
        read_zip(path, Limits(max_entries=1))


def test_zip_normalizes_single_root_without_extraction(tmp_path):
    path = make_zip(tmp_path, [("repo/app.py", "x=1"), ("repo/tests/test_a.py", "x=2")])
    result = read_zip(path)
    assert [f.path for f in result.files] == ["app.py", "tests/test_a.py"]
    assert not (tmp_path / "repo").exists()


def test_non_utf8_and_binary_skipped(tmp_path):
    path = make_zip(tmp_path, [("app.py", "x=1"), ("binary.py", b"\x00"), ("latin.py", b"\xff")])
    result = read_zip(path)
    assert len(result.files) == 1
    assert len(result.skipped) == 2


def test_local_file_and_total_limits(tmp_path):
    (tmp_path / "a.py").write_text("x=1\n" * 10)
    with pytest.raises(AssessmentError, match="size limit"):
        read_local(tmp_path, Limits(max_file_bytes=4))
    with pytest.raises(AssessmentError, match="byte limit"):
        read_local(tmp_path, Limits(max_total_bytes=4))


def test_local_symlink_rejected(tmp_path):
    (tmp_path / "a.py").write_text("x=1")
    try:
        (tmp_path / "b.py").symlink_to(tmp_path / "a.py")
    except OSError:
        pytest.skip("Platform does not permit creating symbolic links.")
    with pytest.raises(AssessmentError):
        read_local(tmp_path)


def test_invalid_or_empty_archive(tmp_path):
    path = tmp_path / "bad.zip"
    path.write_bytes(b"not a zip")
    with pytest.raises(AssessmentError, match="Invalid"):
        read_zip(path)
    with pytest.raises(AssessmentError, match="No supported"):
        read_zip(make_zip(tmp_path, [("image.png", b"image")]))
    with pytest.raises(AssessmentError, match="No supported"):
        read_zip(make_zip(tmp_path, [("node_modules/ignored.py", "x=1")]))


def test_never_executes_source(tmp_path):
    marker = tmp_path / "executed.txt"
    (tmp_path / "app.py").write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('bad')")
    from backend.app.services.assessment import assess
    assess(read_local(tmp_path))
    assert not marker.exists()
