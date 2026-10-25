"""Bounded local / ZIP reading. No extraction, imports, installs or subprocesses."""

import hashlib
import os
from pathlib import Path, PurePosixPath
import stat
import zipfile
import zlib

from backend.app.core.models import AssessmentError, Inventory, Limits, SourceFile

SKIP_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
    "target",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".next",
    "vendor",
}
EXTENSIONS = {
    ".py",
    ".java",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".jsp",
    ".html",
    ".css",
    ".json",
    ".toml",
    ".xml",
    ".gradle",
    ".kts",
    ".properties",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".conf",
    ".sql",
    ".sh",
    ".bat",
    ".txt",
    ".md",
    ".env",
    ".lock",
}
SPECIAL_NAMES = {"dockerfile", "jenkinsfile", "procfile", ".gitignore", ".dockerignore", ".coveragerc"}


def safe_name(name: str, limits: Limits) -> str:
    """Reject ambiguous Windows and POSIX names before considering their content."""
    name = name.replace("\\", "/").rstrip("/")
    parts = name.split("/")
    if (
        not name
        or name.startswith("/")
        or ":" in name
        or any(p in {"", ".", ".."} for p in parts)
        or any(ord(c) < 32 for c in name)
        or len(parts) > limits.max_depth
    ):
        raise AssessmentError("Unsafe repository path or excessive directory depth.")
    return name


def allowed(name: str) -> bool:
    path = PurePosixPath(name)
    return not any(p.lower() in SKIP_DIRS for p in path.parts[:-1]) and (
        path.suffix.lower() in EXTENSIONS or path.name.lower() in SPECIAL_NAMES or path.name.lower().startswith(".env")
    )


def source_file(name: str, raw: bytes, skipped: list[dict]) -> SourceFile | None:
    if b"\x00" in raw:
        skipped.append({"path": name, "reason": "binary content"})
        return None
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        skipped.append({"path": name, "reason": "non-UTF-8 text"})
        return None
    return SourceFile(name, text, len(raw), hashlib.sha256(raw).hexdigest())


def inventory(name: str, kind: str, files: list[SourceFile], skipped: list[dict]) -> Inventory:
    if not files:
        raise AssessmentError("No supported UTF-8 text files were found.")
    files.sort(key=lambda f: f.path)
    digest = hashlib.sha256()
    for file in files:
        digest.update(f"{file.path}\0{file.sha256}\n".encode())
    return Inventory(name, kind, tuple(files), tuple(sorted(skipped, key=lambda s: s["path"])), digest.hexdigest())


def read_local(root: Path, limits: Limits = Limits()) -> Inventory:
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise AssessmentError("Repository must be an existing, non-symlink directory.")
    root = root.resolve()
    files, skipped = [], []
    entries = total = 0

    def walk_error(_: OSError) -> None:
        raise AssessmentError("A repository directory could not be read.")

    for folder, dirs, names in os.walk(root, followlinks=False, onerror=walk_error):
        # Bound directory entries too, including ignored directories at their boundary.
        entries += len(dirs) + len(names)
        if entries > limits.max_entries:
            raise AssessmentError("Repository entry limit exceeded.")
        for dirname in sorted(dirs[:]):
            path = Path(folder) / dirname
            rel = safe_name(path.relative_to(root).as_posix(), limits)
            if path.is_symlink():
                raise AssessmentError("Symbolic links are not accepted.")
            if dirname.lower() in SKIP_DIRS:
                dirs.remove(dirname)
                skipped.append({"path": rel + "/", "reason": "excluded directory"})
        dirs.sort()
        for name in sorted(names):
            path = Path(folder) / name
            rel = safe_name(path.relative_to(root).as_posix(), limits)
            mode = path.lstat().st_mode
            if not stat.S_ISREG(mode):
                raise AssessmentError("Symbolic links and special files are not accepted.")
            if not allowed(rel):
                skipped.append({"path": rel, "reason": "unsupported extension"})
                continue
            if path.stat().st_size > limits.max_file_bytes:
                raise AssessmentError("A supported file exceeds the size limit.")
            # O_NOFOLLOW where available prevents a final-component symlink race.
            fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            with os.fdopen(fd, "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise AssessmentError("Only regular files are accepted.")
                raw = stream.read(limits.max_file_bytes + 1)
            total += len(raw)
            if len(raw) > limits.max_file_bytes or total > limits.max_total_bytes:
                raise AssessmentError("Repository byte limit exceeded.")
            file = source_file(rel, raw, skipped)
            if file:
                files.append(file)
    return inventory(root.name, "local", files, skipped)


def read_zip(path: Path, limits: Limits = Limits()) -> Inventory:
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limits.max_archive_bytes:
        raise AssessmentError("ZIP must be a regular file within the archive size limit.")
    files, skipped = [], []
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > limits.max_entries:
                raise AssessmentError("ZIP entry limit exceeded.")
            names, declared = set(), 0
            validated = []
            for member in members:
                name = safe_name(member.filename, limits)
                if name.casefold() in names:
                    raise AssessmentError("ZIP has duplicate or case-colliding paths.")
                names.add(name.casefold())
                mode = member.external_attr >> 16
                kind = stat.S_IFMT(mode)
                if kind not in {0, stat.S_IFREG, stat.S_IFDIR}:
                    raise AssessmentError("ZIP links and special files are not accepted.")
                if member.flag_bits & 1:
                    raise AssessmentError("Encrypted ZIP entries are not supported.")
                if member.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
                    raise AssessmentError("Only stored or deflated ZIP entries are supported.")
                declared += member.file_size
                if (
                    (allowed(name) and member.file_size > limits.max_file_bytes)
                    or declared > limits.max_total_bytes
                    or member.file_size / max(member.compress_size, 1) > limits.max_compression_ratio
                ):
                    raise AssessmentError("ZIP size or compression-ratio limit exceeded.")
                if not member.is_dir():
                    validated.append((name, member))
            # Normalize a single enclosing folder, so local and ordinary ZIP scans agree.
            file_paths = [PurePosixPath(name) for name, _ in validated]
            roots = {p.parts[0] for p in file_paths}
            strip_root = (
                bool(file_paths)
                and len(roots) == 1
                and not any(root.lower() in SKIP_DIRS for root in roots)
                and all(len(p.parts) > 1 for p in file_paths)
            )
            total = 0
            for name, member in validated:
                if strip_root:
                    name = name.split("/", 1)[1]
                if not allowed(name):
                    skipped.append({"path": name, "reason": "excluded path or unsupported extension"})
                    continue
                with archive.open(member) as stream:
                    raw = stream.read(limits.max_file_bytes + 1)
                total += len(raw)
                if len(raw) > limits.max_file_bytes or total > limits.max_total_bytes:
                    raise AssessmentError("Expanded ZIP byte limit exceeded.")
                file = source_file(name, raw, skipped)
                if file:
                    files.append(file)
    except (zipfile.BadZipFile, RuntimeError, EOFError, NotImplementedError, zlib.error) as exc:
        raise AssessmentError("Invalid, damaged or unsupported ZIP archive.") from exc
    return inventory(path.stem, "zip", files, skipped)
