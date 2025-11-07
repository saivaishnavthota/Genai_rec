@echo off
REM Comprehensive MinIO Fix Script
REM Fixes Docker, MinIO, and video storage issues
echo ========================================
echo MinIO Storage Fix Script
echo ========================================
echo.

REM Step 1: Check Docker Desktop
echo [1/5] Checking Docker Desktop...
docker version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo ERROR: Docker Desktop is NOT running!
    echo ========================================
    echo.
    echo Please:
    echo 1. Start Docker Desktop application
    echo 2. Wait for it to fully start (check system tray icon)
    echo 3. Run this script again
    echo.
    echo ========================================
    pause
    exit /b 1
)
echo    Docker Desktop is running.
echo.

REM Step 2: Check/Remove existing MinIO container
echo [2/5] Checking for existing MinIO container...
docker ps -a --filter "name=minio" --format "{{.Names}}" | findstr /C:"minio" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo    Found existing MinIO container.
    echo    Stopping and removing...
    docker stop minio >nul 2>&1
    docker rm -f minio >nul 2>&1
    echo    Container removed.
) else (
    echo    No existing container found.
)
echo.

REM Step 3: Start MinIO container
echo [3/5] Starting MinIO container...
docker run -d -p 9000:9000 -p 9001:9001 --name minio -e "MINIO_ROOT_USER=minioadmin" -e "MINIO_ROOT_PASSWORD=minioadmin" minio/minio server /data --console-address ":9001"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo ERROR: Failed to start MinIO container!
    echo ========================================
    echo.
    echo Possible issues:
    echo 1. Ports 9000 or 9001 are already in use
    echo    Check: netstat -an ^| findstr "9000 9001"
    echo 2. Docker Desktop needs restart
    echo.
    pause
    exit /b 1
)

echo    MinIO container started.
timeout /t 3 /nobreak >nul
echo.

REM Step 4: Verify MinIO is running
echo [4/5] Verifying MinIO is running...
docker ps --filter "name=minio" --format "{{.Names}}" | findstr /C:"minio" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo    MinIO is running successfully!
) else (
    echo    Warning: MinIO container may not be running properly.
    echo    Check logs: docker logs minio
)
echo.

REM Step 5: Check backend configuration
echo [5/5] Checking backend configuration...
if exist backend\.env (
    echo    Found backend/.env file.
    findstr /C:"MINIO_ENDPOINT" backend\.env >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo    MinIO configuration found in .env file.
    ) else (
        echo    WARNING: MINIO_ENDPOINT not found in backend/.env
        echo    Adding MinIO configuration...
        echo. >> backend\.env
        echo # MinIO Configuration >> backend\.env
        echo MINIO_ENDPOINT=localhost:9000 >> backend\.env
        echo MINIO_ACCESS_KEY=minioadmin >> backend\.env
        echo MINIO_SECRET_KEY=minioadmin >> backend\.env
        echo S3_BUCKET=interview-blobs >> backend\.env
        echo S3_USE_SSL=false >> backend\.env
        echo    Configuration added to backend/.env
    )
) else (
    echo    WARNING: backend/.env file not found!
    echo    Creating backend/.env with MinIO configuration...
    echo # MinIO Configuration > backend\.env
    echo MINIO_ENDPOINT=localhost:9000 >> backend\.env
    echo MINIO_ACCESS_KEY=minioadmin >> backend\.env
    echo MINIO_SECRET_KEY=minioadmin >> backend\.env
    echo S3_BUCKET=interview-blobs >> backend\.env
    echo S3_USE_SSL=false >> backend\.env
    echo    Created backend/.env file
)
echo.

echo ========================================
echo MinIO Setup Complete!
echo ========================================
echo.
echo MinIO Console: http://localhost:9001
echo Login: minioadmin / minioadmin
echo.
echo API Endpoint: http://localhost:9000
echo.
echo IMPORTANT: Restart your backend server for changes to take effect!
echo.
echo Container Status:
docker ps --filter "name=minio" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
echo ========================================
pause

