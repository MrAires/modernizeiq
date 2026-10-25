"""Evidence has stable identifiers and fixed descriptions, never source excerpts."""

import hashlib
from backend.app.core.models import SourceFile


class EvidenceStore:
    def __init__(self) -> None:
        self.evidence: dict[str, dict] = {}
        self.findings: dict[str, dict] = {}
        self.facts: dict[str, list[str]] = {}
        self.warnings: list[dict] = []

    def add(self, rule: str, file: SourceFile | None, line: int | None, description: str) -> str:
        path = file.path if file else "<inventory>"
        key = hashlib.sha256(f"{rule}|{path}|{line}|{description}".encode()).hexdigest()[:14]
        identifier = "ev-" + key
        self.evidence[identifier] = {
            "id": identifier, "rule_id": rule, "file": path, "line": line,
            "file_sha256": file.sha256 if file else None, "description": description,
        }
        return identifier

    def fact(self, key: str, file: SourceFile, line: int | None, description: str) -> str:
        identifier = self.add(key, file, line, description)
        refs = self.facts.setdefault(key, [])
        if identifier not in refs:
            refs.append(identifier)
        return identifier

    def warn(self, file: SourceFile, code: str, message: str) -> None:
        self.warnings.append({"file": file.path, "code": code, "message": message})

    def finding(self, rule: str, file: SourceFile | None, line: int | None,
                category: str, severity: str, title: str, explanation: str,
                action: str, phase: str, effort: str = "Medium", confidence: str = "indicator") -> None:
        evidence_id = self.add(rule, file, line, explanation)
        identifier = "finding-" + evidence_id[3:]
        self.findings[identifier] = {
            "id": identifier, "rule_id": rule, "category": category,
            "severity": severity, "title": title, "explanation": explanation,
            "evidence_ids": [evidence_id], "status": "open", "confidence": confidence,
            "action": action, "phase": phase, "effort": effort,
        }
