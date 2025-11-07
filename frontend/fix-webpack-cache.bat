@echo off
REM Fix MediaPipe Webpack Cache Issue
REM This script clears webpack cache and restarts the dev server
echo ========================================
echo Fixing MediaPipe Webpack Cache Issue
echo ========================================
echo.

echo [1/6] Stopping dev server...
taskkill /F /IM node.exe 2>nul
if %ERRORLEVEL% EQU 0 (
    echo    Dev server stopped.
    timeout /t 2 /nobreak >nul
) else (
    echo    No running Node processes found.
)
echo.

echo [2/6] Clearing React/Webpack cache...
if exist node_modules\.cache (
    rmdir /s /q node_modules\.cache
    echo    Webpack cache cleared.
) else (
    echo    No Webpack cache found.
)
echo.

echo [3/6] Clearing TypeScript cache...
if exist node_modules\.cache\tsconfig (
    rmdir /s /q node_modules\.cache\tsconfig
    echo    TypeScript cache cleared.
)
if exist .tsbuildinfo (
    del /q .tsbuildinfo
    echo    TypeScript build info cleared.
)
echo.

echo [4/6] Verifying MediaPipe package installation...
call npm list @mediapipe/tasks-vision >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    Warning: MediaPipe package may not be installed.
    echo    Reinstalling MediaPipe package...
    call npm install @mediapipe/tasks-vision --save --force
    if %ERRORLEVEL% EQU 0 (
        echo    MediaPipe package reinstalled.
    ) else (
        echo    Error: Failed to reinstall MediaPipe package.
        echo    Please run: npm install
        pause
        exit /b 1
    )
) else (
    echo    MediaPipe package is installed.
)
echo.

echo [5/6] Clearing npm cache...
call npm cache clean --force
echo    npm cache cleared.
echo.

echo [6/6] Cache clearing complete!
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo.
echo 1. Start the dev server:
echo    npm start
echo.
echo 2. If the error persists, run:
echo    fix-mediapipe.bat
echo    (This will do a full clean install)
echo.
echo ========================================
echo.
pause

