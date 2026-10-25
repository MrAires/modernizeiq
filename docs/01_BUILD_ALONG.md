# Build along — understand before claiming

The supplied code is an AI-assisted starting point. Your contribution begins when you run it, trace a result, make a reasoned change, test it and explain the trade-off. Work through one lesson at a time; there is no need to memorize every line.

## Lesson 1 — safe ingestion

**What:** a folder/ZIP reader. **Why:** assessment needs source without trusting its behavior. **Problem:** arbitrary uploads could contain paths outside the project, excessive data or executable content. **Input:** an explicitly selected local folder or ZIP. **Output:** immutable text-file snapshots, hashes and skipped-entry records. **Logic:** validate names/types and limits, read bounded bytes, decode allowed text, sort/hash. **Technology:** Python `pathlib`, `os`, `zipfile`, `hashlib` and dataclasses. **Choice:** standard-library components keep the boundary inspectable and avoid installation inside the target. **Interview point:** reading/parsing a file does not execute its program.

Read `read_local`, `read_zip` and `safe_name` in `backend/app/security/ingestion.py`. The ZIP path never calls extraction. Observe that `.git`, dependencies and build output are excluded. The default limits are 2,000 entries, 512 KiB per supported file, 20 MiB total, 10 MiB compressed ZIP, 100:1 ratio and 20 path segments.

Run the focused checks:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\test_ingestion.py -q
```

Limitations: only UTF-8 text is analyzed. The local folder must not change during scanning; this is not a full OS sandbox. An oversized or unsafe input fails before an assessment is written. Excluded/binary files appear in the scope report.

## Lesson 2 — deterministic inspection

**What:** language, manifest and source inspectors. **Why:** recommendations need observations. **Problem:** guessing from a repository name would be untrustworthy. **Input:** source snapshots. **Output:** languages, dependency declarations, route inventory, facts and selected findings. **Logic:** count recognized source extensions, parse structured manifests, traverse Python AST nodes and apply limited text rules. **Technology:** `ast`, `json`, `tomllib`, XML parsing and bounded regular expressions. **Choice:** AST distinguishes supported Python statements from comments while structured parsers handle manifest syntax. **Interview point:** dependency declarations are not installed/transitive versions, and “old” is not synonymous with “vulnerable.”

Read `parse_dependencies`, `inspect_python`, `inspect_text` and `inspect`. Open `demo-apps/legacy-commerce/config.py`, then find the corresponding file/line evidence in the report. Evidence omits the matched values; file hashes let you recognize a changed snapshot. A malformed Python file produces a warning; it is not silently treated as clean.

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\test_dependencies.py backend\tests\test_assessment.py -q
```

Limitations: aliases, dynamic code, complete Java/JS parsing and interprocedural data flow are not implemented. A SQL-construction indicator needs review before it is called an injection vulnerability. The route inventory does not infer authentication. Dedicated security tooling is still needed for a complete assessment.

## Lesson 3 — transparent scoring

**What:** ten readiness dimensions. **Why:** users need a compact but inspectable summary. **Problem:** arbitrary scores hide judgment. **Input:** observed facts, selected findings and `config/scoring.json`. **Output:** 34 check results, category points and a weighted overall score. **Logic:** earned/possible points, then weighted mean; parser uncertainty removes absence-based credit. **Technology:** Python arithmetic with validated JSON configuration. **Choice:** simple calculations are reproducible and can be checked by hand. **Interview point:** this measures selected indicators, not universal cloud readiness.

For the original fixture, Security earns 40/100: 15 for no selected SQL-construction indicator, 15 for no shell-enabled process indicator and 10 for no wildcard-CORS indicator. It loses 30 for a possible credential, 20 for debug and 10 for HTTP. Security has overall weight 16 out of total weight 100.

Find those checks in the report and verify the arithmetic. Then inspect `score` in `backend/app/scoring/engine.py`. A source-only result cannot prove production safety. Scores can be increased by superficial files; actual behavior must be tested separately.

## Lesson 4 — planning and architecture judgment

**What:** a dependency sketch and prioritized work. **Why:** findings need a useful next action. **Problem:** “rewrite everything as microservices” ignores evidence and effort. **Input:** supported observations and findings. **Output:** low-confidence architecture hypothesis and proposed actions with evidence, priority, phase, qualitative effort/impact and prerequisite references. **Logic:** derive nodes from framework/database/storage/endpoint indicators; group findings by rule; order stabilization before preparation and automation. **Technology:** small Python functions and dictionaries. **Choice:** explicit mappings are easier to review than opaque generated advice. **Interview point:** a modular monolith can be appropriate; independent services need additional business and operational justification.

Read `infer_architecture`, `add_missing_indicators` and `plan`. Follow one recommendation's `finding_ids` and `evidence_ids` in JSON. `validate_references` rejects broken references. No target architecture is implemented automatically and no business costs are estimated. The “proposed” label is not a persistent human-approval workflow.

## Lesson 5 — reporting and command line

**What:** a reusable CLI plus technical and executive outputs. **Why:** a developer and a decision-maker need different detail. **Problem:** JSON alone is hard to demonstrate; a pretty report without evidence is weak. **Input:** the structured assessment. **Output:** `assessment.json`, `assessment.html`, `executive-summary.txt`. **Logic:** escape repository-derived strings, link evidence IDs, show point breakdowns, summarize top actions. **Technology:** Python HTML generation, semantic HTML and structured CSS. **Choice:** an offline report is enough to demonstrate the first milestone before building server state and a React application. **Interview point:** presentation consumes the same assessment; it does not invent findings.

Read `main`, `write_outputs`, `render_html` and `executive_text`. Expand risks and score calculations, follow evidence links and use your browser's Print command for the light layout. This is a report viewer, not the final live workbench. It has no upload, login, database or review-decision endpoint.

## Lesson 6 — testing and evaluation

**What:** an automated correctness suite and controlled benchmark. **Why:** an assessment must handle both true and false indications. **Problem:** a demonstration can appear accurate if it reads its answers or only tests positive cases. **Input:** fixtures and expected labels stored separately. **Output:** passing/failing checks, matched/missed/extra findings and per-category precision/recall. **Logic:** run the analyzer first, compare `(rule, file, line)` triples after it finishes. **Technology:** pytest and a standalone evaluator. **Choice:** tests isolate behavior; the evaluator measures a specific labelled sample. **Interview point:** 11/11 on a tiny synthetic fixture is not 100% real-world accuracy.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check backend benchmarks
.\.venv\Scripts\python.exe -m benchmarks.evaluate
```

`null` precision/recall means an empty denominator, not failure or invented 100%. The improved control has no expected positives, so recall is undefined. The test suite was generated with the starter; do not claim to have written it independently. Add your own regression case and explain why it would have caught an error.

## Hands-on experiment A — one setting, predicted score change

From the project root in PowerShell:

```powershell
Copy-Item -Recurse demo-apps\legacy-commerce demo-apps\my-commerce
```

1. Open `demo-apps/my-commerce/config.py` in VS Code.
2. Before editing, record your prediction: disabling debug removes the debug finding and earns 20 Security points. Overall should rise by `20 × 16/100 = 3.2`, from 22.2 to 25.4.
3. Change only `DEBUG = True` to `DEBUG = False`. Save.
4. Run:

```powershell
.\.venv\Scripts\python.exe -m backend.app.cli analyze --repo demo-apps\my-commerce --out runs\debug-disabled
```

5. Open `runs/debug-disabled/assessment.html`. Expect 10 findings and a 25.4 overall heuristic. The credential and local-state problems should still be present.
6. Record the observed result in `docs/MY_LEARNING_LOG.md`. If it differs, inspect what else changed instead of rewriting your prediction.

Why this helps: you connect one source change to one rule, one check and the weighted final score. That is a defensible technical explanation.

## Hands-on experiment B — externalize configuration

In the same copied `config.py`, add `import os` below the docstring. Replace the three literal assignments with:

```python
DATABASE_PASSWORD = os.environ["DATABASE_PASSWORD"]
DATABASE_URL = os.environ["DATABASE_URL"]
PAYMENT_URL = os.environ["PAYMENT_URL"]
```

Predict: the source no longer exposes those literal values; credential, endpoint and configuration-local-state findings should disappear. `storage.py` still writes locally, so local persistence is not fully removed. Environment configuration checks should gain credit.

```powershell
.\.venv\Scripts\python.exe -m backend.app.cli analyze --repo demo-apps\my-commerce --out runs\external-config
```

You do not need to set environment variables to **analyze** this source because it is never imported or run. In a real deployed app, values would need to be provided safely at runtime. Externalization alone does not supply secret rotation, access controls or durability.

## Hands-on experiment C — change scoring priorities

```powershell
Copy-Item config\scoring.json config\my-scoring.json
```

Change only `category_weights.Security` from 16 to 25. Predict that Security matters more in the weighted mean, without changing detected findings. Run the unchanged original fixture with the custom file:

```powershell
.\.venv\Scripts\python.exe -m backend.app.cli analyze --repo demo-apps\legacy-commerce --scoring config\my-scoring.json --out runs\security-weighted
```

Compare `findings` and `readiness` in the JSON. The configuration SHA-256 changes. Explain why increasing a dimension's weight can raise or lower the overall score depending on how that dimension compares with the other dimensions. Do not tune weights just to advertise a better number.

## Hands-on experiment D — add a regression test

Add `backend/tests/test_my_regression.py`:

```python
from backend.app.security.ingestion import read_local
from backend.app.services.assessment import assess

def test_disabled_debug_is_not_flagged(tmp_path):
    (tmp_path / "app.py").write_text("DEBUG = False\n")
    result = assess(read_local(tmp_path))
    assert "DEBUG_ENABLED" not in {f["rule_id"] for f in result["findings"]}
```

Run it, then explain why this negative case matters. Temporarily change the fixture line to `DEBUG = True`: the assertion should fail. Restore it and run the full suite. This is a meaningful hands-on test of a rule boundary, even if similar coverage already exists in the supplied suite.

## Hands-on experiment E — inspect your own project

Choose a small repository you are allowed to analyze. Make a local snapshot, run the CLI, and inspect at least three findings manually. Mark each as confirmed, intentional or false positive in your learning log. Do not place confidential source or reports in a public GitHub repository. Record one unsupported case; explaining limits is part of engineering.

## What to keep as evidence of your work

Your predictions, edited source, test you added, real command output, before/after reports, and screenshots you captured. Commit a small, understandable change with its reason. Be ready to reproduce it without following a generated script blindly.
