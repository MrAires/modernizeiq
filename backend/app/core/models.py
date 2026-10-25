"""Small immutable input models. Repository contents never become executable code."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Limits:
    max_entries: int = 2000
    max_file_bytes: int = 512 * 1024
    max_total_bytes: int = 20 * 1024 * 1024
    max_archive_bytes: int = 10 * 1024 * 1024
    max_compression_ratio: int = 100
    max_depth: int = 20


@dataclass(frozen=True)
class SourceFile:
    path: str
    text: str = field(repr=False)
    size: int
    sha256: str


@dataclass(frozen=True)
class Inventory:
    name: str
    source_kind: str
    files: tuple[SourceFile, ...]
    skipped: tuple[dict, ...]
    fingerprint: str


class AssessmentError(ValueError):
    """Expected input failure suitable for a concise CLI error."""
