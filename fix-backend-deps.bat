@echo off
REM Quick Fix: Install missing packages in running backend container
echo ========================================
echo Installing Missing Packages in Backend
echo ========================================
echo.

echo Installing minio package...
docker-compose exec backend pip install minio>=7.2.0

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Package installed successfully!
    echo Restarting backend...
    docker-compose restart backend
    echo.
    echo Backend should now be running.
) else (
    echo.
    echo Failed to install package.
    echo The container might not be running.
    echo.
    echo Try: docker-compose up -d backend
)

pause

