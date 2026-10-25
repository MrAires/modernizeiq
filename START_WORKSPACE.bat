@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
echo Run SETUP_WORKSPACE.bat first.
pause
exit /b 1
)
echo Open http://127.0.0.1:8012
echo Keep this window open. Press Ctrl+C to stop.
".venv\Scripts\python.exe" -m uvicorn backend.app.workspace:app --host 127.0.0.1 --port 8012
pause

