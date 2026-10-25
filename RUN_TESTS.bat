@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run SETUP_MODERNIZEIQ.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pytest -q
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m ruff check backend benchmarks
if errorlevel 1 goto :failed
if not exist runs mkdir runs
".venv\Scripts\python.exe" -m benchmarks.evaluate > runs\benchmark-results.json
if errorlevel 1 goto :failed
echo Tests and lint passed. Read runs\benchmark-results.json for the measured fixture evaluation.
pause
exit /b 0
:failed
echo Verification failed. Read the error above; do not report this run as passing.
pause
exit /b 1
