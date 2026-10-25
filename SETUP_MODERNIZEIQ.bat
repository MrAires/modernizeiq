@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher not found. Install Python 3.11 or newer with the Windows launcher.
  pause
  exit /b 1
)
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
  echo Python 3.11 or newer is required.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 goto :failed
echo SETUP COMPLETE. Run RUN_DEMO.bat, then RUN_TESTS.bat.
echo Do not install requirements from the demo-apps folders.
pause
exit /b 0
:failed
echo Setup failed. Read the error above; check Python and the internet connection.
pause
exit /b 1
