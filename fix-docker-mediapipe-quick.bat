@echo off
REM Quick fix: Install MediaPipe inside running container
echo ========================================
echo Quick Fix: Installing MediaPipe in Container
echo ========================================
echo.

echo [1/2] Installing @mediapipe/tasks-vision in container...
docker-compose exec frontend npm install @mediapipe/tasks-vision --save
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install package
    echo Trying alternative method...
    docker exec genai-frontend npm install @mediapipe/tasks-vision --save
)
echo.

echo [2/2] Restarting frontend container...
docker-compose restart frontend
echo.

echo ========================================
echo Installation complete!
echo ========================================
echo.
echo Check logs with: docker-compose logs -f frontend
echo.
pause

