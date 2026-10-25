# ModernizeIQ Studio

**25 October update:** see [UPDATE_NOTES.md](UPDATE_NOTES.md), [WHAT_TO_SELECT.md](WHAT_TO_SELECT.md), and LEARNING_GUIDE.docx for the fixes and hands-on instructions.

Understand application evidence. Plan a modernization you can explain.

**Start with [START_HERE.md](START_HERE.md).** Run SETUP_WORKSPACE.bat, then START_WORKSPACE.bat, and open http://127.0.0.1:8012. A fresh workspace loads a working demo automatically.

## Delivered in this release

- Distinct ivory/plum identity, custom M logo, serif headlines, horizontal navigation, and responsive layouts.
- Twelve navigation pages: portfolio, workbench, architecture, dependencies, risks, transformation plan, decisions, comparison, reports, audit, import, and guide.
- Real repository ZIP ingestion, evidence-linked findings, transparent readiness checks, dependency inventory, and phased recommendations.
- Baseline and improved-control demos; every new upload creates a persistent assessment.
- SQLite history, searchable/filterable registers, detailed evidence drawers, human reviews, and audit records.
- Comparison of saved snapshots, printable reports, JSON evidence exports, and spreadsheet-safe CSV exports.
- Hands-on exercises, backend tests, optional reproducible browser workflow tests, and editable SVG branding.

## Implementation

The current workspace uses Python, FastAPI, SQLite, and modular static HTML/CSS/JavaScript served by the backend. It does not require a frontend build step or a hosted AI service. The analysis engine uses deterministic source inspection and configurable scoring.

| Location | Responsibility |
| --- | --- |
| backend/app/workspace.py | Input validation, imports, persistence, review APIs, and UI routes |
| backend/app/workspace_features.py | Idempotent demos, downloadable inputs, printable and CSV reports |
| workspace_ui/app.js | Page rendering, input forms, filters, charts, comparison, and review interactions |
| workspace_ui/styles.css | Product-specific design tokens, layouts, responsive and print styles |
| workspace_ui/logo.svg | Editable product mark |
| backend/tests | Backend behavior and regression checks |
| scripts/test_studio_browser.py | Optional end-to-end browser check using an isolated temporary database |

Read [LEARNING_AND_DEMO.md](LEARNING_AND_DEMO.md) for a guided demonstration, practical experiment, and accurate résumé framing. [WORKSPACE_VERIFICATION.md](WORKSPACE_VERIFICATION.md) states what was tested.

## Boundaries

This is a local single-user application, not a production-certified hosted SaaS. Readiness scores are heuristics; dependency vulnerability status is not checked. Uploaded source is never executed. Human decisions are recorded without executing remediation.

Existing historical tooling is retained for learning. [docs/LEGACY_README.md](docs/LEGACY_README.md) describes the earlier release; use the current startup guide for Studio.
"# modernizeiq" 
