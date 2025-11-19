@echo off
title GenAI Frontend Server
cd frontend

echo.
echo ================================================================================
echo                          🚀 Starting Frontend Server
echo ================================================================================
echo.

REM Check if node_modules exists
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        echo 💡 Make sure Node.js is installed and in PATH
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed
) else (
    echo ✅ Dependencies already installed
)

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  .env file not found in frontend directory
    echo 💡 Make sure REACT_APP_API_URL is set in environment or .env
)

REM Kill any existing processes on port 3000
echo.
echo 🔧 Checking for existing processes on port 3000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING 2^>nul') do (
    echo    Found process on port 3000 (PID: %%a), killing it...
    taskkill /F /PID %%a >nul 2>&1
    timeout /t 1 /nobreak >nul
)

REM Run the server
echo.
echo 🚀 Starting React development server...
echo    Frontend URL: http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo    (If port is still in use, run: kill-frontend-port.bat)
echo.

call npm start

REM Cleanup on exit
echo.
echo 🔧 Cleaning up...
taskkill /F /IM node.exe >nul 2>&1
echo    Frontend server stopped.

pause

