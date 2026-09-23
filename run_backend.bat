@echo off
setlocal
cd /d "%~dp0backend"
set "TASK_BACKEND_PORT=%~1"
if not defined TASK_BACKEND_PORT set "TASK_BACKEND_PORT=8000"
set "TASK_FRONTEND_PORT=%~2"
if not defined TASK_FRONTEND_PORT set "TASK_FRONTEND_PORT=5173"
set "FRONTEND_ORIGIN=http://localhost:%TASK_FRONTEND_PORT%"
if not exist .venv\Scripts\python.exe python -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
if not exist .env copy .env.example .env >nul
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port %TASK_BACKEND_PORT%
