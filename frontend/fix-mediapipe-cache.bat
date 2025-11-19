@echo off
REM Fix MediaPipe TypeScript/Webpack cache issue
echo ========================================
echo Fixing MediaPipe Cache Issue
echo ========================================
echo.

echo [1/5] Stopping dev server...
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul
echo.

echo [2/5] Clearing React/Webpack cache...
if exist node_modules\.cache (
    rmdir /s /q node_modules\.cache
    echo    React cache cleared.
) else (
    echo    No React cache found.
)
echo.

echo [3/5] Clearing TypeScript cache...
if exist node_modules\.cache\tsconfig (
    rmdir /s /q node_modules\.cache\tsconfig
    echo    TypeScript cache cleared.
)
if exist .tsbuildinfo (
    del /q .tsbuildinfo
    echo    TypeScript build info cleared.
)
echo.

echo [4/5] Clearing npm cache...
call npm cache clean --force
echo    npm cache cleared.
echo.

echo [5/5] Reinstalling MediaPipe package...
call npm install @mediapipe/tasks-vision --save --force
if %ERRORLEVEL% EQU 0 (
    echo    MediaPipe reinstalled.
) else (
    echo    Warning: Reinstall had issues, trying full clean install...
    echo.
    echo    Running full clean install...
    call clean-install.bat
    exit /b 0
)
echo.

echo Verifying installation...
call npm list @mediapipe/tasks-vision
echo.

echo ========================================
echo Cache cleared and package reinstalled!
echo ========================================
echo.
echo Now restart your dev server:
echo   npm start
echo.
pause

