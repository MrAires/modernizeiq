# Contributing

Start with a small supported pattern and its negative counterexample. Use fictional input. Document the rule's scope, source location, false-positive risks and human follow-up. Keep matched secrets and source snippets out of reports. Do not execute inspected code.

Run `python -m pytest -q` and `python -m ruff check backend benchmarks` with the project's environment. Add a behavioral regression test when changing analysis or ingestion. Keep expected benchmark labels outside `demo-apps/`; justify label changes independently from actual analyzer output. Update the walkthrough and scoring documentation when behavior changes.

Do not label future API, persistence, AI or UI stages as completed. Keep report colors consistent with the warm enterprise palette.
