# Choose the right input

| App | Start page | Select this file | Settings | Expected observation |
| --- | --- | --- | --- | --- |
| OpsPilot, port 8011 | Data sources | samples/01_incident_telemetry.csv | latency 1000, error 0.05, samples 3, gap 120 | 2 sustained episodes across 6 services |
| OpsPilot | Data sources | samples/01_healthy_telemetry.csv | same settings | 0 episodes |
| OpsPilot | Data sources | samples/01_transient_telemetry.csv | same settings | isolated spikes; 0 sustained episodes |
| ModernizeIQ, port 8012 | New assessment | samples/02_baseline_repository.zip | name: Baseline; objective: inspect legacy patterns | baseline findings and evidence |
| ModernizeIQ | New assessment | samples/02_improved_repository.zip | name: Improved control | higher fixture readiness; not a real-world security guarantee |
| EvoSkill, port 8013 | Tasks | samples/backend_learning.json | review filled fields and submit | production proposal is blocked before execution |
| EvoSkill | Tasks | samples/intern_scope_control.json | review and submit | backend skill is not reused for intern |
| AgentLedger, port 8014 | New transaction | samples/approval_timeout.json | retain defaults for first run | timeout then bounded retry then human approval |
| AgentLedger | New transaction | samples/compensation_failure.json | advance 5 times, open Recovery | PO compensated; account compensation fails; manual review |

For the new projects, selecting JSON fills the form; click Create to submit. In OpsPilot/ModernizeIQ, click Analyze and save. Run each project from its own folder and environment. Use SETUP_WORKSPACE.bat and START_WORKSPACE.bat for the first two; SETUP.bat and START.bat for the new two.

OpsPilot accepts measurements (CSV or JSON), not project ZIPs. ModernizeIQ accepts a source ZIP and never executes it. Source scans and telemetry investigations answer different questions.

Changing settings can change findings without fixing a system. Higher readiness on the small improved fixture does not imply that the four full repositories have that score. Re-import after an analyzer update; retained snapshots do not change retroactively.
