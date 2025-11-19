@echo off
REM Kill processes using port 3000 (Frontend)
echo ========================================
echo Killing Frontend Port (3000)
echo ========================================
echo.

REM Find processes using port 3000
echo [1/3] Finding processes on port 3000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    set PID=%%a
    echo    Found process with PID: %%a
)

if not defined PID (
    echo    No process found on port 3000.
    echo    Port is already free.
    echo.
    pause
    exit /b 0
)

REM Kill the process
echo.
echo [2/3] Killing process PID: %PID%...
taskkill /F /PID %PID% >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo    Process killed successfully.
) else (
    echo    Warning: Could not kill process %PID%
    echo    Trying alternative method...
    taskkill /F /IM node.exe >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo    All Node.js processes killed.
    ) else (
        echo    Could not kill processes. You may need admin rights.
    )
)

REM Also kill any remaining Node processes (in case there are multiple)
echo.
echo [3/3] Checking for remaining Node.js processes...
tasklist /FI "IMAGENAME eq node.exe" 2>NUL | find /I /N "node.exe">NUL
if %ERRORLEVEL% EQU 0 (
    echo    Found additional Node.js processes.
    echo    Killing all Node.js processes...
    taskkill /F /IM node.exe >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo    All Node.js processes killed.
    )
) else (
    echo    No additional Node.js processes found.
)

echo.
echo ========================================
echo Port 3000 should now be free!
echo ========================================
echo.
echo Verifying port is free...
timeout /t 1 /nobreak >nul
netstat -aon | findstr :3000 | findstr LISTENING >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo    WARNING: Port 3000 is still in use!
    echo    You may need to run this script as Administrator.
) else (
    echo    Port 3000 is now free.
)
echo.
pause

