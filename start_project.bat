@echo off
setlocal
set "TASK_BACKEND_PORT=%~1"
if not defined TASK_BACKEND_PORT set "TASK_BACKEND_PORT=8000"
set "TASK_FRONTEND_PORT=%~2"
if not defined TASK_FRONTEND_PORT set "TASK_FRONTEND_PORT=5173"
start "Alem Backend" cmd /k ""%~dp0run_backend.bat" %TASK_BACKEND_PORT% %TASK_FRONTEND_PORT%"
start "Alem Frontend" cmd /k ""%~dp0run_frontend.bat" %TASK_FRONTEND_PORT% %TASK_BACKEND_PORT%"
