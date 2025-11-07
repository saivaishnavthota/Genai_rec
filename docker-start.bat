@echo off
REM Start Complete Application on Docker
echo ========================================
echo Starting Complete Application on Docker
echo ========================================
echo.

REM Check Docker
echo [1/4] Checking Docker...
docker version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    ERROR: Docker Desktop is not running!
    echo    Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo    Docker is running.
echo.

REM Check .env file
echo [2/4] Checking environment file...
if not exist .env (
    echo    WARNING: .env file not found!
    echo    Creating from env.example...
    if exist env.example (
        copy env.example .env >nul
        echo    Created .env file. Please update values if needed.
    ) else (
        echo    ERROR: env.example not found!
        pause
        exit /b 1
    )
) else (
    echo    .env file found.
)
echo.

REM Stop any existing containers
echo [3/4] Stopping existing containers...
docker-compose down >nul 2>&1
echo    Cleaned up existing containers.
echo.

REM Start services
echo [4/4] Starting all services...
echo    This may take a few minutes on first run...
echo.
docker-compose up -d --build

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Application Started Successfully!
    echo ========================================
    echo.
    echo Services:
    echo   Frontend:  http://localhost:3000
    echo   Backend:   http://localhost:8000
    echo   API Docs:  http://localhost:8000/docs
    echo   MinIO:     http://localhost:9001 (minioadmin/minioadmin)
    echo.
    echo View logs: docker-compose logs -f
    echo Stop:     docker-compose down
    echo.
    echo Checking service status...
    timeout /t 5 /nobreak >nul
    docker-compose ps
    echo.
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Failed to start services!
    echo ========================================
    echo.
    echo Check logs: docker-compose logs
    echo.
    pause
    exit /b 1
)

pause

