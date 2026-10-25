# ModernizeIQ Studio — start here

This is the current interactive release. Use **SETUP_WORKSPACE.bat** and **START_WORKSPACE.bat**. Earlier launchers and documentation remain for historical features; they do not launch this redesigned interface.

## Windows: first launch

1. Stop any old server with Ctrl+C. Extract the entire ZIP into a **new folder**, then open the modernizeiq folder. Do not run it inside the compressed ZIP.
2. Install Python 3.11 or newer with the Windows Python launcher if it is not already installed. Check `py -3 --version`.
3. Double-click **SETUP_WORKSPACE.bat** once. Internet is needed to install dependencies. Wait for “Setup complete.”
4. Double-click **START_WORKSPACE.bat**. Keep that terminal open.
5. Open **http://127.0.0.1:8012/portfolio** in your browser. Use Ctrl+F5 if an older interface is cached.
6. An empty workspace automatically loads the demonstration. If you already have records, click **Explore demo**. Your existing imports and decisions are preserved.

You do not need Node, an API key, a paid AI account, or a separate database server for this workspace. Run each project from its own folder and virtual environment.

## Your first five-minute demonstration

1. Open **Portfolio**. The baseline has 11 findings and a 22.2/100 readiness heuristic.
2. Open **Workbench**, then click a readiness dimension to inspect the individual checks and earned points.
3. Open **Architecture**. Switch between observed structure and proposed review areas; click a node to inspect evidence.
4. Open **Dependencies** and search for a package. Open **Risk register** and inspect a finding.
5. Open **Transformation plan** to see phased actions and prerequisites.
6. In **Decisions**, select a finding, enter a rationale, and choose Accept, Reject, Defer, or Investigate. **Audit trail** records it.
7. In **Compare assessments**, compare the baseline to the improved control. The control scores 96.3/100 with zero matching findings. Those scores describe these fixtures and rules, not real production readiness.
8. Open **Reports** for a printable report, JSON evidence package, and CSV register.

The examples run through the same analysis engine as user imports. Demo records are clearly labelled. “Explore demo” is safe to repeat; it does not overwrite your work.

## Bring your own input

Open **New assessment**, upload a source repository ZIP, and enter a project name, objective, and business criticality. The program statically inspects supported source/configuration files without executing the uploaded application. Archives must fit the documented upload and expanded-content limits. Dependency versions are declarations; vulnerability advisories are **not checked**.

Business criticality is review context; it does not secretly change technical evidence. Use **Download sample** on the import page for a valid starting file.

## Learn by changing something

Download the sample ZIP, extract it, and change `DEBUG = True` to `DEBUG = False` in config.py. Predict which finding and score will change. ZIP the source again and import it under a new name. Compare with the baseline, inspect the evidence, and write down why other findings remain. Do not install or run the intentionally weak demo application's dependencies.

Record your hypothesis, exact change, result, and limitation. Then add one meaningful input-validation or detector/analyzer test of your own. See **LEARNING_AND_DEMO.md** for the problem statement, code map, and interview practice.

## Data and troubleshooting

- Saved runs and decisions live in **data/workspace.sqlite3**. Stop the server before copying that file for backup. The ZIP excludes development/test databases.
- To carry over data from the previous practical workspace, stop both servers and copy your old data/workspace.sqlite3 into the new project's data folder before starting. Keep the original backup.
- “Address already in use”: stop the old terminal server for port 8012, then start this one. Ports 8011 and 8012 let the projects run together.
- “Workspace could not load”: keep START_WORKSPACE.bat running and inspect its error. Refresh with Ctrl+F5.
- Import rejected: read the inline message, check the format and size, and try the downloadable sample.
- Close the terminal or press Ctrl+C to stop. Changes to source code require a server restart; CSS/JavaScript changes require a browser refresh.

## Linux/macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-workspace.txt
.venv/bin/python -m uvicorn backend.app.workspace:app --host 127.0.0.1 --port 8012
```

## Verification and scope

Run `.venv\Scripts\python.exe -m pytest backend/tests -q` on Windows, or `.venv/bin/python -m pytest backend/tests -q` on Linux/macOS. The delivered suite passed 66 tests. See **WORKSPACE_VERIFICATION.md** for exact test scope and optional browser checks.

This is a functioning local, single-user research/portfolio application. Its static checks and readiness scores are explainable heuristics, not proof of security or deployment success. Review decisions do not execute infrastructure changes. Public hosted sales require authentication, tenant isolation, operational hardening, security review, and customer validation; this ZIP does not claim those are complete.

