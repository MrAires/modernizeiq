@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run SETUP_MODERNIZEIQ.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m backend.app.cli analyze --repo demo-apps\improved-control --out runs\improved-control --overwrite
if errorlevel 1 (
  echo Assessment failed. Read the error above.
  pause
  exit /b 1
)
start "" "%~dp0runs\improved-control\assessment.html"
pause
