@echo off
REM Fix MediaPipe package installation - Clean install
echo ========================================
echo Clean Install - Fixing MediaPipe Package
echo ========================================
echo.

REM Stop any running dev server
echo [1/4] Stopping any running Node processes...
taskkill /F /IM node.exe 2>nul
if %ERRORLEVEL% EQU 0 (
    echo    Dev server stopped.
    timeout /t 2 /nobreak >nul
) else (
    echo    No running Node processes found.
)
echo.

REM Remove node_modules
echo [2/4] Removing node_modules directory...
if exist node_modules (
    rmdir /s /q node_modules
    echo    node_modules removed successfully.
) else (
    echo    node_modules directory not found (already clean).
)
echo.

REM Remove package-lock.json
echo [3/4] Removing package-lock.json...
if exist package-lock.json (
    del /q package-lock.json
    echo    package-lock.json removed.
) else (
    echo    package-lock.json not found.
)
echo.

REM Clear npm cache
echo [4/4] Clearing npm cache...
call npm cache clean --force
echo    npm cache cleared.
echo.

REM Install all dependencies
echo ========================================
echo Installing all dependencies...
echo This may take a few minutes...
echo ========================================
call npm install

echo.
echo ========================================
if %ERRORLEVEL% EQU 0 (
    echo Installation completed successfully!
    echo.
    echo Verifying MediaPipe package...
    call npm list @mediapipe/tasks-vision
    echo.
    echo You can now start the dev server with: npm start
) else (
    echo Installation failed. Please check the errors above.
)
echo ========================================
echo.
pause

