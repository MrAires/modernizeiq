"""Selected AST and text indicators, intentionally not a general security scanner."""

import ast
from collections import Counter
from pathlib import PurePosixPath
import re

from backend.app.analyzers.evidence import EvidenceStore
from backend.app.core.models import Inventory, SourceFile

LANGUAGES = {".py": "Python", ".java": "Java", ".js": "JavaScript", ".jsx": "JavaScript",
             ".ts": "TypeScript", ".tsx": "TypeScript", ".jsp": "JSP"}
FRAMEWORKS = {"flask": "Flask", "django": "Django", "fastapi": "FastAPI", "react": "React",
              "express": "Express", "org.springframework:spring-webmvc": "Spring MVC",
              "org.springframework.boot:spring-boot-starter-web": "Spring Boot"}
SECRET_KEY = re.compile(r"(?:password|passwd|pwd|secret|token|api[_-]?key)", re.I)
PLACEHOLDER = re.compile(r"^(?:\*+|<.*>|\$\{.*\}|changeme|replace[_ -]?me|your[_-].*|example|placeholder)$", re.I)

ISSUES = {
    "SECRET_LITERAL": ("Security", "high", "Possible embedded credential",
                       "A credential-like key has a literal value. The value is omitted from this assessment.",
                       "Confirm the finding; rotate a real exposed credential and use a managed secret reference.", "Stabilize", "Medium"),
    "HARDCODED_URL": ("Configuration", "medium", "Embedded endpoint configuration",
                      "An HTTP(S) endpoint literal appears in source or configuration. Its value is omitted.",
                      "Make environment-specific endpoints configurable; document any intentional fixed public endpoint.", "Stabilize", "Low"),
    "HTTP_ENDPOINT": ("Security", "medium", "Unencrypted HTTP endpoint indicator",
                      "A literal endpoint uses HTTP. Whether it carries sensitive traffic requires review.",
                      "Review the trust boundary and use TLS for sensitive traffic.", "Stabilize", "Low"),
    "DEBUG_ENABLED": ("Security", "high", "Debug configuration enabled",
                      "A debug setting is enabled in an inspected configuration or run call.",
                      "Disable debug mode in deployment configuration and test the production startup path.", "Stabilize", "Low"),
    "LOCAL_STORAGE": ("Architecture", "medium", "Local persistence dependency",
                      "A local write, local database or absolute storage path suggests instance-bound state.",
                      "Verify durability requirements; consider managed relational or object storage for shared state.", "Prepare", "Medium"),
    "CORS_WILDCARD": ("Security", "medium", "Wildcard CORS configuration",
                      "A CORS-related setting appears to allow every origin.",
                      "Restrict allowed origins according to the application's authentication and trust model.", "Stabilize", "Low"),
    "SQL_CONSTRUCTION": ("Security", "high", "Dynamic SQL construction indicator",
                         "An execute call receives interpolated or concatenated text; data flow is not proven.",
                         "Review parameter binding and add a test for untrusted input. Confirm before labelling an injection vulnerability.", "Stabilize", "Medium"),
    "SHELL_ENABLED": ("Security", "high", "Shell-enabled process call",
                      "A process call enables shell interpretation. Input controllability was not analyzed.",
                      "Prefer argument arrays without a shell; review any required shell boundary.", "Stabilize", "Medium"),
    "SECRET_FILE": ("Security", "medium", "Environment file included in scan",
                    "A non-template .env file is present in this snapshot; commit history and value sensitivity are unknown.",
                    "Check repository tracking and keep real secrets out of version control.", "Stabilize", "Low"),
}


def issue(store: EvidenceStore, rule: str, file: SourceFile, line: int | None) -> None:
    store.finding(rule, file, line, *ISSUES[rule])


def dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return dotted(node.value) + "." + node.attr
    return ""


def inspect_python(file: SourceFile, store: EvidenceStore) -> tuple[set[str], list[dict]]:
    imports: set[str] = set()
    routes = []
    try:
        tree = ast.parse(file.text)
    except (SyntaxError, ValueError, RecursionError):
        store.warn(file, "python-syntax", "Python syntax was not parsed; AST indicators are incomplete for this file.")
        return imports, routes
    for node in ast.walk(tree):
        line = getattr(node, "lineno", None)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = [n.name for n in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            imports.update(name.split(".")[0] for name in modules)
            if any(name.split(".")[0] in {"logging", "structlog", "loguru"} for name in modules):
                store.fact("logging", file, line, "A logging library import is present.")
            if any(name.split(".")[0] in {"prometheus_client", "opentelemetry"} for name in modules):
                store.fact("telemetry", file, line, "A metrics or tracing library import is present.")
            if any(name.split(".")[0] in {"sqlite3", "psycopg", "psycopg2", "pymysql"} for name in modules):
                store.fact("db_import", file, line, "A database driver import is present.")
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            for target in targets:
                key = dotted(target)
                if isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant):
                    key = str(target.slice.value)
                if re.search(r"cors|allow.?origins", key, re.I) and isinstance(value, (ast.List, ast.Tuple)):
                    if any(isinstance(v, ast.Constant) and v.value == "*" for v in value.elts):
                        issue(store, "CORS_WILDCARD", file, line)
                if isinstance(value, ast.Constant):
                    if SECRET_KEY.search(key) and isinstance(value.value, str) and value.value and not PLACEHOLDER.fullmatch(value.value):
                        issue(store, "SECRET_LITERAL", file, line)
                    if key.lower().endswith("debug") and value.value is True:
                        issue(store, "DEBUG_ENABLED", file, line)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if re.match(r"https?://", value):
                issue(store, "HARDCODED_URL", file, line)
                if value.startswith("http://"):
                    issue(store, "HTTP_ENDPOINT", file, line)
            if value.startswith(("sqlite:///", "/var/", "/tmp/", "/opt/", "C:\\")):
                issue(store, "LOCAL_STORAGE", file, line)
            if "sqlite" in value.lower():
                store.fact("db_sqlite", file, line, "A SQLite configuration indicator is present.")
            if re.match(r"(?:jdbc:)?(?:postgres(?:ql)?|mysql)(?:\+\w+)?://", value):
                store.fact("db_relational", file, line, "A relational database endpoint indicator is present.")
        if isinstance(node, ast.Call):
            call = dotted(node.func)
            for keyword in node.keywords:
                if keyword.arg and re.search(r"cors|allow.?origins", keyword.arg, re.I) and isinstance(keyword.value, (ast.List, ast.Tuple)):
                    if any(isinstance(v, ast.Constant) and v.value == "*" for v in keyword.value.elts):
                        issue(store, "CORS_WILDCARD", file, line)
            if call in {"os.getenv", "os.environ.get", "getenv"}:
                store.fact("env_config", file, line, "An environment configuration read is present.")
            if call.endswith(".run") and any(k.arg == "debug" and isinstance(k.value, ast.Constant) and k.value.value is True for k in node.keywords):
                issue(store, "DEBUG_ENABLED", file, line)
            if call.startswith("subprocess.") and any(k.arg == "shell" and isinstance(k.value, ast.Constant) and k.value.value is True for k in node.keywords):
                issue(store, "SHELL_ENABLED", file, line)
            if call.endswith((".execute", ".executemany")) and node.args:
                if isinstance(node.args[0], (ast.JoinedStr, ast.BinOp)):
                    issue(store, "SQL_CONSTRUCTION", file, line)
                store.fact("raw_sql", file, line, "A direct SQL execution call is present.")
            mode = node.args[1] if call == "open" and len(node.args) > 1 else None
            if call in {"open", "Path.open"} or call.endswith(".open"):
                mode = next((k.value for k in node.keywords if k.arg == "mode"), mode)
                if isinstance(mode, ast.Constant) and isinstance(mode.value, str) and any(c in mode.value for c in "wax+"):
                    issue(store, "LOCAL_STORAGE", file, line)
            if call.endswith((".write_text", ".write_bytes")):
                issue(store, "LOCAL_STORAGE", file, line)
        if isinstance(node, ast.Subscript) and dotted(node.value) == "os.environ":
            store.fact("env_config", file, line, "An environment configuration read is present.")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not decorator.args:
                    continue
                method = dotted(decorator.func).split(".")[-1]
                value = decorator.args[0]
                if method not in {"route", "get", "post", "put", "delete", "patch"} or not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                    continue
                route = value.value
                # Do not copy arbitrary strings/queries from untrusted decorators into the report.
                display = route if re.fullmatch(r"/[A-Za-z0-9_/{}/:<>.\-]*", route) else "[route omitted]"
                methods = [method.upper()] if method != "route" else ["GET"]
                for keyword in decorator.keywords:
                    if keyword.arg == "methods" and isinstance(keyword.value, (ast.List, ast.Tuple)):
                        methods = [v.value.upper() for v in keyword.value.elts if isinstance(v, ast.Constant) and isinstance(v.value, str) and v.value.upper() in {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}]
                ref = store.fact("api_route", file, decorator.lineno, "A supported web-route decorator is present.")
                routes.append({"methods": methods, "route": display, "handler": node.name,
                               "file": file.path, "line": decorator.lineno, "authentication": "not inferred",
                               "evidence_ids": [ref]})
                if route in {"/health", "/healthz", "/ready", "/readyz"}:
                    store.fact("health", file, decorator.lineno, "A conventional health/readiness route is declared; behavior is unverified.")
    return imports, routes


def inspect_text(file: SourceFile, store: EvidenceStore) -> None:
    suffix = PurePosixPath(file.path).suffix.lower()
    if suffix not in {".properties", ".env", ".ini", ".cfg", ".conf", ".java", ".js", ".ts", ".json", ".yaml", ".yml"} and not PurePosixPath(file.path).name.startswith(".env"):
        return
    if PurePosixPath(file.path).name in {"package.json", "package-lock.json"}:
        return
    for number, raw in enumerate(file.text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(("#", "//", "*")):
            continue
        secret = re.search(r'''(?i)["']?([\w.-]*(?:password|passwd|secret|token|api[_-]?key)[\w.-]*)["']?\s*[:=]\s*["']?([^\s,"';}]+)''', line)
        if secret and not PLACEHOLDER.fullmatch(secret.group(2)) and "${" not in secret.group(2) and not re.search(r"getenv|process\.env|environ|System\.get", line):
            issue(store, "SECRET_LITERAL", file, number)
        if re.search(r"https?://", line):
            issue(store, "HARDCODED_URL", file, number)
        if "http://" in line:
            issue(store, "HTTP_ENDPOINT", file, number)
        if re.search(r'''(?i)debug["']?\s*[:=]\s*(?:true|1)\b''', line):
            issue(store, "DEBUG_ENABLED", file, number)
        if re.search(r"/var/|/tmp/|/opt/|sqlite:///|[A-Z]:\\", line):
            issue(store, "LOCAL_STORAGE", file, number)
        if re.search(r"(?i)(cors|allow.?origins).*[\"']\*[\"']", line):
            issue(store, "CORS_WILDCARD", file, number)
        if re.search(r"process\.env|System\.getenv|\$\{\w+\}", line):
            store.fact("env_config", file, number, "An environment configuration reference is present.")


def inspect(inventory: Inventory, dependencies: list[dict], store: EvidenceStore) -> dict:
    counts: Counter = Counter()
    imports: set[str] = set()
    routes: list[dict] = []
    for file in inventory.files:
        path = PurePosixPath(file.path)
        name = path.name.lower()
        if path.suffix.lower() in LANGUAGES:
            counts[LANGUAGES[path.suffix.lower()]] += 1
        if path.suffix.lower() == ".py":
            found, api = inspect_python(file, store)
            imports |= found
            routes.extend(api)
        else:
            inspect_text(file, store)
        def fact(key: str, description: str) -> None:
            store.fact(key, file, None, description)
        if name.startswith("test_") or name.endswith(("_test.py", ".test.ts", ".test.js", ".spec.ts")) or "tests" in path.parts:
            fact("tests", "A test-named file is present; tests were not executed.")
        if name.startswith(".env") and not name.endswith((".example", ".sample", ".template")):
            issue(store, "SECRET_FILE", file, None)
        if name == "dockerfile":
            fact("docker", "A Dockerfile is present; image construction was not tested.")
            if re.search(r"(?mi)^\s*(CMD|ENTRYPOINT)\s", file.text):
                fact("docker_start", "A container startup instruction is present.")
            if re.search(r"(?mi)^\s*HEALTHCHECK\s+(?!NONE\b)", file.text):
                fact("container_health", "A Docker healthcheck instruction is present.")
        is_ci = (".github/workflows/" in file.path and path.suffix in {".yml", ".yaml"}) or name in {".gitlab-ci.yml", "jenkinsfile", "azure-pipelines.yml"}
        if is_ci:
            fact("ci", "A recognized CI configuration file is present.")
            if re.search(r"pytest|unittest|npm\s+(?:run\s+)?test|mvn\s+test|gradle\s+test", file.text):
                fact("ci_tests", "CI text includes a test command; execution was not verified.")
            if re.search(r"docker\s+build|build-push-action", file.text):
                fact("ci_container", "CI text includes a container build indicator.")
        if name.startswith("readme"):
            fact("readme", "A README file is present.")
        if name == ".coveragerc" or (name == "pyproject.toml" and "[tool.coverage" in file.text):
            fact("coverage_config", "Coverage configuration is present; coverage was not executed or measured.")
        if "deploy" in name or "operations" in name:
            fact("deployment_docs", "A deployment/operations-named file is present.")
        if name in {"security.md", "contributing.md"}:
            fact("governance_docs", "A security or contributor guide is present.")
        if name in {"package-lock.json", "poetry.lock", "uv.lock", "pipfile.lock", "yarn.lock"}:
            fact("lockfile", "A recognized lockfile is present; resolved contents were not audited.")
        if any(part.lower() in {"services", "controllers", "repositories", "models"} for part in path.parts[:-1]):
            fact("layers", "A conventional layer directory is present; separation is not proven.")
        if any(part.lower() in {"migrations", "alembic"} for part in path.parts):
            fact("migrations", "A migration-tool directory is present.")
        if len(file.text.splitlines()) > 500:
            store.finding("LARGE_FILE", file, None, "Architecture", "low", "Large source or configuration file",
                          "An inspected text file exceeds 500 lines; responsibility concentration needs review.",
                          "Inspect responsibilities and split only where cohesive module boundaries exist.", "Modernize", "Medium")
    declared = {d["name"].lower() for d in dependencies}
    frameworks = sorted({label for key, label in FRAMEWORKS.items() if key in declared | imports})
    for framework in frameworks:
        matching = next((d for d in dependencies if FRAMEWORKS.get(d["name"].lower()) == framework), None)
        if matching:
            store.facts.setdefault("framework", []).extend(matching["evidence_ids"])
    db = []
    for keys, label in [({"sqlite3"}, "SQLite"), ({"psycopg", "psycopg2", "psycopg2-binary"}, "PostgreSQL"), ({"pymysql", "mysqlclient"}, "MySQL")]:
        if (declared | imports) & keys or (label == "SQLite" and store.facts.get("db_sqlite")):
            db.append(label)
    if store.facts.get("db_relational") and not db:
        db.append("Relational database (endpoint indicator)")
    return {"primary_language": sorted(counts, key=lambda k: (-counts[k], k))[0] if counts else "Unknown",
            "language_file_counts": dict(sorted(counts.items())), "frameworks": frameworks,
            "databases": db, "api_inventory": sorted(routes, key=lambda r: (r["file"], r["line"])),
            "test_files": len(store.facts.get("tests", [])), "coverage": "not measured",
            "files_analyzed": len(inventory.files), "dependencies_declared": len(dependencies)}
