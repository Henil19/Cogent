@echo off
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
echo =======================================================
echo Starting Cogent Research Platform (Development Mode)
echo =======================================================
echo Starting FastAPI Backend on http://localhost:8000 ...
start "Cogent Backend" cmd /k "cd /d ""%SCRIPT_DIR%backend"" && .venv\Scripts\activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting React Frontend on http://localhost:5173 ...
start "Cogent Frontend" cmd /k "cd /d ""%SCRIPT_DIR%frontend"" && npm run dev"

echo =======================================================
echo Cogent is launching:
echo   - Research Cockpit: http://localhost:5173
echo   - Interactive Swagger API: http://localhost:8000/docs
echo =======================================================
