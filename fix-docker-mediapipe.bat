@echo off
REM Fix MediaPipe in Docker - Rebuild frontend container
echo ========================================
echo Fixing MediaPipe in Docker Container
echo ========================================
echo.

echo [1/3] Stopping frontend container...
docker-compose stop frontend
echo.

echo [2/3] Rebuilding frontend container with MediaPipe...
docker-compose build --no-cache frontend
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build frontend container
    pause
    exit /b 1
)
echo.

echo [3/3] Starting frontend container...
docker-compose up -d frontend
echo.

echo ========================================
echo Frontend container rebuilt!
echo ========================================
echo.
echo Checking container logs...
docker-compose logs --tail=50 frontend
echo.
pause

