# ModernizeIQ

**Understand the legacy. Plan the transformation.**

ModernizeIQ analyzes application evidence and assists modernization assessment and planning. This delivery is **milestone 1: a working deterministic assessment**, as requested in the supplied prompt's first task. It is a local Python prototype with JSON, executive-text and graphite/copper HTML reports. It does not yet include an LLM, FastAPI server, SQLite history or React workbench.

## Problem

Before modernizing an application, a team needs to understand its technology, dependencies, configuration and operational barriers. Manual review can be repetitive and hard to trace. ModernizeIQ gathers selected static indicators, explains its scoring and proposes evidence-linked work for human judgment.

## Run on Windows

1. Install Python **3.11 or newer**, including the Windows `py` launcher.
2. Extract this ZIP. Open the `modernizeiq` folder.
3. Double-click `SETUP_MODERNIZEIQ.bat` once. This creates `.venv` and installs development/test tools. Internet is needed for this setup only.
4. Double-click `RUN_DEMO.bat`. It analyzes the bundled source and opens the HTML report.
5. Double-click `RUN_TESTS.bat` to verify the analyzer.

To preview immediately without installing anything, open `samples/legacy-assessment/assessment.html`. That is a pre-generated sample, not a new scan. **Do not install the demo application's requirements.**

## Run from a terminal

From the `modernizeiq` project root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m backend.app.cli analyze --repo demo-apps\legacy-commerce --out runs\first-assessment
.\.venv\Scripts\python.exe -m pytest -q
```

macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m backend.app.cli analyze --repo demo-apps/legacy-commerce --out runs/first-assessment
.venv/bin/python -m pytest -q
```

Only tests and lint need third-party tools. The analyzer itself uses Python's standard library. It never installs the inspected repository's dependencies.

Scan your own local repository or ZIP:

```powershell
.\.venv\Scripts\python.exe -m backend.app.cli analyze --repo C:\Projects\my-application --out runs\my-assessment
.\.venv\Scripts\python.exe -m backend.app.cli analyze --zip C:\Downloads\application.zip --out runs\zip-assessment
```

Quote paths containing spaces. Choose an output directory outside the scanned repository. Existing report files are protected unless you explicitly pass `--overwrite`. Use an immutable local copy while scanning.

## Implemented features

- Bounded folder/ZIP ingestion; no extraction or code execution.
- File inventory, hashes, skipped-file accounting and language file counts.
- Declared dependencies from requirements, pyproject, package.json, Maven and literal Gradle coordinates.
- Selected Python AST and configuration-text indicators, with masked evidence.
- Limited API decorator inventory, framework/database indicators and an inferred architecture sketch.
- Ten readiness dimensions with 34 documented, configurable point checks.
- Rule-driven priorities, phase ordering and prerequisite references.
- Offline HTML evidence inspection, JSON export and executive summary.
- Controlled benchmark plus positive, negative, security-boundary and integration tests.

## Architecture and data flow

`security/ingestion.py` creates an immutable snapshot. `analyzers/` gathers declarations, facts and findings. `services/assessment.py` orchestrates analysis without knowing benchmark answers. `scoring/engine.py` produces auditable points from `config/scoring.json`. `recommendations/planner.py` groups findings into proposed actions. `services/report.py` escapes output for the offline report. `cli.py` writes outputs. The evaluator reads ground truth separately.

## Scoring methodology

Category score = `100 × earned points / possible points`. Overall = weighted mean of category scores. Presence checks earn points only when observed. Absence checks earn points when the corresponding selected indicator is not found; parser warnings make otherwise clean absence checks unknown with zero credit. All evidence is scope-limited. The exported JSON includes the scoring configuration hash and every contribution.

This is a configurable modernization-readiness heuristic. A high score is not a security certificate, measured coverage or proof that Docker/CI actually works. Presence checks can be superficial; the improved fixture deliberately makes that limitation visible.

## Sample assessment and verification

The original legacy fixture contains 7 supported files, 2 dependency declarations and 11 labelled findings. Its default score is 22.2/100. The improved control has 12 files, no findings from these selected rules, and a score of 96.3/100. The remaining unearned points reflect absent telemetry and lockfile indicators. These scores concern source indicators, not deployed systems.

The packaged test run passed 51 tests on Python 3.12.14; lint passed. See `docs/VERIFICATION.md` and `docs/test-results.txt`. Windows batch launchers require verification on your machine. No GUI screenshot, Docker build, hosted deployment or real-world accuracy claim is made. Sample HTML reports are provided instead of fabricated screenshots.

## API and full product status

There is no API server in this milestone. The planned FastAPI groups, SQLite entities and React information architecture are documented in `docs/00_PRODUCT_AND_ARCHITECTURE.md`. `frontend/README.md` records the future workbench design contract. These components must be implemented and tested before being claimed on a résumé.

## Security and limitations

See `SECURITY.md`. Source is inspected statically; arbitrary scripts, binaries and dependency installs are never run. Reports contain fixed descriptions and locations, not source snippets or detected secret values. Scans are limited to supported UTF-8 text and small repositories. Static architecture, security and operational indicators require confirmation. Vulnerability/deprecation/age checks, transitive dependency resolution, runtime behavior, business impact and costs are not determined.

## Learn and demonstrate

Start with `START_HERE.md`, follow `docs/01_BUILD_ALONG.md`, inspect `docs/02_CODE_WALKTHROUGH.md`, then use `docs/03_INTERVIEW_AND_RESUME.md`. Keep your own experiment notes in `docs/MY_LEARNING_LOG.md`. Only add claims to your résumé after you can reproduce and explain the behavior.

## Roadmap, contributing and license

The ordered product roadmap and acceptance gates are in the architecture specification. Contributions should include a concrete input, predicted output and a test proving the rule's boundary; see `CONTRIBUTING.md`. MIT license; see `LICENSE`.
