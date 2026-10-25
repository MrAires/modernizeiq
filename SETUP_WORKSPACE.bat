@echo off
setlocal
cd /d "%~dp0"
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 goto :failed
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m pip install -r requirements-workspace.txt
if errorlevel 1 goto :failed
echo Setup complete. Run START_WORKSPACE.bat.
pause
exit /b 0
:failed
echo Setup failed. Python 3.11 or newer and internet for installation are required.
pause
exit /b 1

