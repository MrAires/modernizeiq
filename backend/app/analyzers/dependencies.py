"""Read declared dependencies only. Never install, resolve or query registries."""

import json
from pathlib import PurePosixPath
import re
import tomllib
import xml.etree.ElementTree as ET

from backend.app.analyzers.evidence import EvidenceStore
from backend.app.core.models import SourceFile

NAME = re.compile(r"^[A-Za-z0-9@][A-Za-z0-9_.:@/\-]{0,160}$")
SPEC = re.compile(r"^[A-Za-z0-9 .,^~<>=!*+|\-\[\](){}$]{0,160}$")
REQ = re.compile(r"^([A-Za-z0-9][A-Za-z0-9_.-]*)(?:\[[^]]+\])?\s*(.*)$")


def parse_dependencies(files: tuple[SourceFile, ...], store: EvidenceStore) -> list[dict]:
    result: list[dict] = []

    def add(file: SourceFile, name: str, version: object, ecosystem: str, scope: str) -> None:
        if not isinstance(name, str) or not NAME.fullmatch(name):
            store.warn(file, "dependency-name", "A dependency name was omitted because its syntax is unsupported.")
            return
        value = str(version).split(";", 1)[0].strip()
        # URLs, credentials and arbitrary values are deliberately not exported.
        safe_version = value if SPEC.fullmatch(value) else "[reference omitted]"
        line = next((i for i, text in enumerate(file.text.splitlines(), 1) if name in text), None)
        ref = store.fact("dependency_manifest", file, line, "A dependency declaration was parsed.")
        pinned = bool(re.fullmatch(r"(?:==)?\d+(?:\.\d+)+(?:[-+._A-Za-z0-9]*)", safe_version))
        result.append({"name": name, "version": safe_version or "unspecified", "ecosystem": ecosystem,
                       "scope": scope, "file": file.path, "line": line, "pinned": pinned,
                       "evidence_ids": [ref], "vulnerability_status": "not checked",
                       "outdated_status": "not checked", "deprecated_status": "not checked"})
        if not pinned:
            store.finding("DEP_UNPINNED", file, line, "Dependency Health", "low",
                          "Dependency version is not an exact release",
                          "A declaration uses a range, indirect reference or unspecified version; a lockfile may resolve it.",
                          "Review lockfile and reproducibility policy; do not assume this package is vulnerable.",
                          "Prepare", "Low")

    for file in files:
        name = PurePosixPath(file.path).name.lower()
        try:
            if name.startswith("requirements") and name.endswith(".txt"):
                for line in file.text.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("-"):
                        store.warn(file, "requirements-directive", "An install option or included file directive was not followed.")
                        continue
                    match = REQ.match(line.split(" #", 1)[0])
                    if match:
                        add(file, *match.groups(), "Python", "development" if "dev" in name else "runtime")
                    else:
                        store.warn(file, "requirements-syntax", "An unsupported dependency declaration was omitted.")
            elif name == "package.json":
                data = json.loads(file.text)
                if not isinstance(data, dict):
                    raise ValueError
                for group in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
                    entries = data.get(group, {})
                    if not isinstance(entries, dict):
                        raise ValueError
                    for dep, version in entries.items():
                        add(file, dep, version, "npm", group)
            elif name == "pyproject.toml":
                data = tomllib.loads(file.text)
                project = data.get("project", {})
                lists = [("runtime", project.get("dependencies", []))]
                lists.extend((f"optional:{key}", values) for key, values in project.get("optional-dependencies", {}).items())
                for scope, entries in lists:
                    if not isinstance(entries, list):
                        raise ValueError
                    for entry in entries:
                        match = REQ.match(entry) if isinstance(entry, str) else None
                        if match:
                            add(file, *match.groups(), "Python", scope)
                poetry = data.get("tool", {}).get("poetry", {})
                groups = [("runtime", poetry.get("dependencies", {}))]
                groups.extend((f"group:{key}", group.get("dependencies", {}))
                              for key, group in poetry.get("group", {}).items())
                for scope, entries in groups:
                    for dep, declaration in entries.items():
                        if dep.lower() == "python":
                            continue
                        version = declaration.get("version", "[reference omitted]") if isinstance(declaration, dict) else declaration
                        add(file, dep, version, "Python", scope)
            elif name == "pom.xml":
                if "<!DOCTYPE" in file.text.upper() or "<!ENTITY" in file.text.upper():
                    store.warn(file, "xml-dtd", "XML with a DTD or entity declaration was not parsed.")
                    continue
                root = ET.fromstring(file.text)
                # Dependency-management and transitive dependencies are not resolved.
                for node in root.findall("./{*}dependencies/{*}dependency"):
                    group = node.findtext("{*}groupId", "")
                    artifact = node.findtext("{*}artifactId", "")
                    add(file, f"{group}:{artifact}", node.findtext("{*}version", ""), "Maven", node.findtext("{*}scope", "compile"))
            elif name in {"build.gradle", "build.gradle.kts"}:
                for match in re.finditer(r'''(?m)^\s*(implementation|api|compileOnly|runtimeOnly|testImplementation)\s*\(?\s*["']([\w.-]+):([\w.-]+):([^"']+)["']''', file.text):
                    scope, group, artifact, version = match.groups()
                    add(file, f"{group}:{artifact}", version, "Gradle", scope)
                store.warn(file, "gradle-limited", "Only literal Gradle coordinates were inspected; scripts were not evaluated.")
        except (ValueError, TypeError, AttributeError, ET.ParseError):
            store.warn(file, "manifest-parse", "A manifest could not be fully parsed; dependency inventory may be incomplete.")
    seen: set[tuple] = set()
    unique = []
    for dep in result:
        key = (dep["file"], dep["name"], dep["version"], dep["scope"])
        if key not in seen:
            seen.add(key)
            unique.append(dep)
    return sorted(unique, key=lambda d: (d["ecosystem"], d["name"].lower(), d["file"], d["scope"]))
