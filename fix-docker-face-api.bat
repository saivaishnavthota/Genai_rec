@echo off
REM Fix face-api.js in Docker - Rebuild frontend container
echo ========================================
echo Installing face-api.js in Docker Container
echo ========================================
echo.

echo [1/4] Stopping frontend container...
docker-compose stop frontend
echo.

echo [2/4] Installing @vladmandic/face-api in container...
docker-compose exec -T frontend npm install @vladmandic/face-api --save --legacy-peer-deps 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Trying alternative method...
    docker exec genai-frontend npm install @vladmandic/face-api --save --legacy-peer-deps
)
echo.

echo [3/4] Rebuilding frontend container...
docker-compose build --no-cache frontend
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build frontend container
    pause
    exit /b 1
)
echo.

echo [4/4] Starting frontend container...
docker-compose up -d frontend
echo.

echo ========================================
echo Frontend container rebuilt with face-api.js!
echo ========================================
echo.
echo Checking container logs...
timeout /t 3 /nobreak >nul
docker-compose logs --tail=30 frontend
echo.
echo If you see compilation errors, wait a moment for npm install to complete.
echo.
pause

