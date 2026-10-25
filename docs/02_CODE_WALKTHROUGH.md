# Code walkthrough and design decisions

## Trace one complete result

1. `cli.main` parses `--repo` or `--zip`, output and optional scoring configuration.
2. `read_local` / `read_zip` validates and builds an `Inventory` of `SourceFile` values.
3. `assessment.assess` creates an `EvidenceStore`, calls `parse_dependencies`, then `inspect`.
4. For `DEBUG = True`, `inspect_python` sees an AST assignment with a constant boolean. It calls `issue("DEBUG_ENABLED", ...)`.
5. `EvidenceStore.finding` stores a fixed explanation and line reference; `EvidenceStore.add` computes a stable evidence ID. The source value is not copied to a report.
6. `add_missing_indicators` adds scope-level findings such as no recognized CI file.
7. `infer_architecture` builds explicitly inferred nodes/relationships.
8. `score` evaluates configured facts and finding absence. Debug means the Security debug check earns zero out of 20.
9. `plan` groups matching findings into proposed actions with evidence and prerequisite references.
10. `validate_references` checks referential integrity before serialization.
11. `write_outputs` produces JSON, escaped HTML and a short executive text file.

## Important files

| File | Main concept | How to inspect/test |
|---|---|---|
| `core/models.py` | immutable inputs and centralized safety limits | Read dataclasses; limit tests |
| `security/ingestion.py` | trust boundary and bounded static reads | `test_ingestion.py` |
| `analyzers/evidence.py` | stable IDs, traceability, fixed descriptions | evidence/reference tests |
| `analyzers/dependencies.py` | declared dependency parsers | `test_dependencies.py` |
| `analyzers/inspection.py` | AST traversal and limited text indicators | source/negative-control tests |
| `scoring/engine.py` | validation, points, weighted mean | manual arithmetic and config tests |
| `config/scoring.json` | adjustable weights/checks | experiment C |
| `recommendations/planner.py` | grouping and dependency-aware sequence | follow recommendation IDs |
| `services/assessment.py` | orchestration and architecture hypothesis | deterministic/reference tests |
| `services/report.py` / `report.css` | safe presentation and warm design | HTML escaping test; open sample |
| `cli.py` | user interface and explicit overwrite policy | `test_cli.py` |
| `benchmarks/evaluate.py` | evaluation isolated from analysis | compare labelled triples |

## Why these decisions

The baseline uses Python 3.11+ so TOML parsing needs no runtime dependency. AST traversal is more precise for supported Python syntax than scanning all text; pattern rules remain useful for limited non-Python configuration. ZIP contents stay in memory, so archive members never choose output paths. JSON is sufficient for the first milestone; pretending to have SQL before history exists adds little learning value. An offline HTML report makes evidence explorable without a server. The final React/FastAPI architecture is planned separately.

## Common failure cases

Malformed manifests warn rather than fabricate dependencies. Unsupported Gradle logic is not executed. Comment/placeholder handling reduces some false positives but cannot infer runtime intent. Alias imports and dynamic function construction may hide routes. Multiple packages in a monorepo are summarized together; service boundaries are not resolved. CI/Docker/test files can exist without working. Local reads are not race-proof across concurrently changed parent directories; use a fixed copy. Public hostile uploads need worker isolation and resource quotas beyond these application-level limits.

## Data deliberately not inferred

Real credentials, dependency vulnerability status, deprecation or latest release, actual test coverage, production environment, complete network calls, authentication strength, exact business impact, migration duration and cloud cost. These require evidence beyond static patterns. The application never connects to a discovered database or endpoint.

## How to extend responsibly

Pick a concrete input pattern, add a positive fixture and a negative counterexample, define a fixed redacted description, implement the smallest detector, add a score check only if its interpretation is justified, and update documentation. Keep analyzer inputs independent from evaluation labels. Do not introduce an LLM until the deterministic contract and evidence validator are stable.
