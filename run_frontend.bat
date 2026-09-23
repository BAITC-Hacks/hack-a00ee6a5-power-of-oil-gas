@echo off
setlocal
cd /d "%~dp0frontend"
set "TASK_FRONTEND_PORT=%~1"
if not defined TASK_FRONTEND_PORT set "TASK_FRONTEND_PORT=5173"
set "TASK_BACKEND_PORT=%~2"
if not defined TASK_BACKEND_PORT set "TASK_BACKEND_PORT=8000"
set "VITE_API_URL=http://localhost:%TASK_BACKEND_PORT%/api"
if not exist node_modules call npm ci
if errorlevel 1 exit /b 1
if not exist .env copy .env.example .env >nul
call npm run dev -- --port %TASK_FRONTEND_PORT% --strictPort
