@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0generate_samples.ps1"
echo.
pause
