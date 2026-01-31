@echo off
REM AutoBI - Quick Start (opens both servers in separate windows)
echo Starting AutoBI...
echo.

start "AutoBI Backend" cmd /k "%~dp0start-backend.bat"
timeout /t 3 /nobreak >nul
start "AutoBI Frontend" cmd /k "%~dp0start-frontend.bat"

echo.
echo Both servers are starting in separate windows.
echo.
echo Access the application at: http://localhost:3000
echo API documentation at: http://localhost:8000/docs
echo.
pause
