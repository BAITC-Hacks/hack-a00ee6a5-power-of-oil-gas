@echo off
start "AI SANA Backend" cmd /k "%~dp0run_backend.bat"
start "AI SANA Frontend" cmd /k "%~dp0run_frontend.bat"
