# Verification — 24 October 2026

## Executed checks

- Python 3.12.14, Linux environment.
- `python -m pytest -q`: **51 passed**. Raw output: `test-results.txt`.
- `python -m ruff check backend benchmarks`: **passed**.
- CLI analyzed both fixtures and produced JSON, HTML and executive-text outputs.
- Evaluation matched **11 of 11** labelled legacy findings with **0 extra findings**, and detected **0 findings** on the improved control. Per-category counts/precision/recall: `benchmark-results.json`.
- The documented one-variable experiment was executed in a temporary copy: setting `DEBUG=False` produced **10 findings** and **25.4/100**, versus 11 findings and 22.2/100 before the change.

The two small fixtures are the evaluation population. These results do not estimate accuracy on arbitrary real repositories. The improved control's precision and recall are `null` because there are no detected/expected positive findings; undefined values are not replaced with invented percentages.

## What the tests cover

Unsafe ZIP names, symlinks, compression/size/count limits, excluded-directory handling, no extraction and no source execution; supported dependency declarations and malformed manifests; secret-value omission and negative controls; selected AST indicators; deterministic evidence, line/hash consistency, reference validation and score arithmetic; configurable weights, escaped HTML and CLI overwrite/input-output boundaries.

## What remains unverified or unimplemented

Windows batch scripts are supplied but were not executed in this Linux environment. Browser appearance needs a local visual check; a passing HTML/content check is not a browser interaction test. No Docker image was built. No target dependency was installed. No inspected application's tests or deployment were run. No cloud deployment or real-world benchmark was performed. The full React, FastAPI, SQL history, review workflow and LLM product stages are planned rather than included.

## Reproduce

Run setup, then `RUN_TESTS.bat`, or use the three commands in the build-along guide. If you change rules, fixtures or weights, record a fresh result instead of citing these numbers unchanged.
