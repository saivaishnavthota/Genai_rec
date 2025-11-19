@echo off
REM Start MinIO for AI Interview Storage
REM This script removes any existing MinIO container and starts a fresh one
echo ========================================
echo MinIO Container Management
echo ========================================
echo.

REM Check if Docker is available
echo [0/4] Checking Docker availability...
docker version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo ERROR: Docker is not available!
    echo ========================================
    echo.
    echo Docker Desktop is not running or not accessible.
    echo.
    echo Please:
    echo 1. Start Docker Desktop application
    echo 2. Wait for it to fully start (check system tray icon)
    echo 3. Run this script again
    echo.
    echo To check Docker status, run:
    echo   docker ps
    echo.
    echo ========================================
    pause
    exit /b 1
)
echo    Docker is available.
echo.

REM Check if MinIO container exists (running or stopped)
echo [1/4] Checking for existing MinIO container...
docker ps -a --filter "name=minio" --format "{{.Names}}" | findstr /C:"minio" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo    Found existing MinIO container.
    echo.
    echo [2/3] Stopping and removing existing container...
    docker stop minio >nul 2>&1
    docker rm -f minio >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo    Container removed successfully.
    ) else (
        echo    Warning: Could not remove container (may not exist).
    )
) else (
    echo    No existing MinIO container found.
    echo    Skipping removal step.
)
echo.

REM Start new MinIO container
echo [3/4] Starting new MinIO container...
docker run -d -p 9000:9000 -p 9001:9001 --name minio -e "MINIO_ROOT_USER=minioadmin" -e "MINIO_ROOT_PASSWORD=minioadmin" minio/minio server /data --console-address ":9001"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [4/4] Verifying container is running...
    timeout /t 2 /nobreak >nul
    docker ps --filter "name=minio" --format "{{.Names}}" | findstr /C:"minio" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo    Container is running.
        echo.
        echo ========================================
        echo MinIO started successfully!
        echo ========================================
        echo.
        echo Access MinIO Console at: http://localhost:9001
        echo Login: minioadmin / minioadmin
        echo.
        echo API Endpoint: http://localhost:9000
        echo.
        echo Container Status:
        docker ps --filter "name=minio" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo.
        echo ========================================
    ) else (
        echo    Warning: Container may not have started properly.
        echo    Check Docker logs: docker logs minio
    )
) else (
    echo.
    echo ========================================
    echo Failed to start MinIO container!
    echo ========================================
    echo.
    echo Possible issues:
    echo 1. Docker Desktop is not running
    echo    - Start Docker Desktop application
    echo    - Wait for it to fully initialize
    echo.
    echo 2. Ports 9000 or 9001 are already in use
    echo    - Check: netstat -an | findstr "9000 9001"
    echo    - Stop the process using those ports
    echo.
    echo 3. Docker daemon is not accessible
    echo    - Restart Docker Desktop
    echo    - Check: docker ps
    echo.
    echo To check Docker status:
    echo   docker ps
    echo.
    echo To check if ports are in use:
    echo   netstat -an | findstr "9000 9001"
    echo.
    echo To view container logs (if created):
    echo   docker logs minio
    echo.
    echo ========================================
)

pause
