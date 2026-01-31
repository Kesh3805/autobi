@echo off
REM AutoBI - Start Frontend Server
echo Starting AutoBI Frontend Server...
echo.

cd /d "%~dp0frontend"

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

echo.
echo Frontend starting at http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo.

npm run dev
