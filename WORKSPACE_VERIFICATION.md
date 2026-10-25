# Studio verification — 24 October 2026

## Executed checks

Environment: Linux, Python 3.12, Chromium 134 through Playwright.

- Complete backend suite: **66 tests passed**.
- The five added product tests verify repeatable demo loading without losing decisions, demo controls, sample import round trips, printable/CSV exports, escaped report content, and served brand/UI assets.
- Browser workflow: all **12 navigation pages** rendered at desktop width 1440 and narrow width 390 without page-level horizontal overflow or JavaScript page errors.
- Browser interactions passed: demo load/reload, project and finding filters, evidence drawers, two successive human decisions with latest status and retained history, snapshot comparison, same-snapshot guard, printable report, JSON/CSV responses, sample file upload, and persisted new assessment.
- Also checked score breakdown drawers, architecture view switching and proposed-node details, package filtering, and populated phased recommendations.
- Desktop screenshots were visually inspected internally. They are not bundled as product data.

## Reproduce

From the project directory:

```bash
python -m pytest backend/tests -q
```

Optional browser test (separate development dependency):

```bash
python -m pip install playwright
python -m playwright install chromium
python scripts/test_studio_browser.py
```

The browser check starts a temporary server on 127.0.0.1:8090 and an isolated temporary SQLite database. Port 8090 must be available. It does not change your normal database. BROWSER_EXECUTABLE can point to an existing compatible Chromium binary.

## Limits of this verification

Windows launch scripts were reviewed but not executed on Windows. Mobile checks used a browser viewport rather than physical devices. A test-client dependency deprecation warning was emitted; no test failed. No public deployment, load test, formal accessibility audit, independent security audit, or external customer validation is claimed. Earlier verification documents describe historical releases.
