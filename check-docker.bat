@echo off
REM Check Docker Desktop status
echo ========================================
echo Docker Desktop Status Check
echo ========================================
echo.

echo Checking if Docker is installed...
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker is not installed!
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
docker --version
echo.

echo Checking if Docker daemon is running...
docker ps >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo ERROR: Docker Desktop is not running!
    echo ========================================
    echo.
    echo Please:
    echo 1. Start Docker Desktop from Start Menu
    echo 2. Wait for Docker to fully initialize (watch system tray icon)
    echo 3. When Docker icon shows "Docker Desktop is running", try again
    echo.
    echo To verify Docker is running, you should see:
    echo   docker ps
    echo.
    echo This should list running containers (may be empty).
    echo.
    echo ========================================
    pause
    exit /b 1
)

echo Docker daemon is running!
echo.
echo Running containers:
docker ps
echo.
echo All containers (including stopped):
docker ps -a
echo.
echo ========================================
echo Docker is ready to use!
echo ========================================
pause

