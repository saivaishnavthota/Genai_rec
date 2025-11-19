@echo off
REM Stop Complete Application on Docker
echo ========================================
echo Stopping Application on Docker
echo ========================================
echo.

docker-compose down

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Application stopped successfully!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Failed to stop services!
    echo ========================================
)

echo.
pause

