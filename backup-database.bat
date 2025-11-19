@echo off
setlocal enabledelayedexpansion
title GenAI Database Backup

echo.
echo ================================================================================
echo                          📦 GenAI Database Backup Tool
echo ================================================================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Create backup directory
if not exist "database\backups" mkdir database\backups

REM Generate timestamp for backup filename
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set mydate=%%c-%%a-%%b
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set mytime=%%a%%b
set mytime=!mytime: =!
set timestamp=!mydate!_!mytime!

set backup_file=database\backups\genai_hiring_backup_!timestamp!.sql

echo 🔍 Creating database backup...
echo 📁 Backup file: !backup_file!

REM Create SQL dump
docker-compose exec -T postgres pg_dump -U postgres -d genai_hiring --clean --if-exists --create > "!backup_file!"

if errorlevel 1 (
    echo ❌ Backup failed!
    pause
    exit /b 1
) else (
    echo ✅ Database backup created successfully!
    echo 📁 Location: !backup_file!
    
    REM Get file size
    for %%A in ("!backup_file!") do set size=%%~zA
    echo 📊 Size: !size! bytes
)

echo.
echo 🎯 Backup Options:
echo    1. View backup file content
echo    2. Copy backup to another location
echo    3. Exit
echo.
set /p choice=Enter your choice (1-3): 

if "!choice!"=="1" (
    echo.
    echo 📄 Opening backup file...
    notepad "!backup_file!"
) else if "!choice!"=="2" (
    echo.
    set /p dest=Enter destination path: 
    copy "!backup_file!" "!dest!" >nul
    if errorlevel 1 (
        echo ❌ Copy failed!
    ) else (
        echo ✅ Backup copied to !dest!
    )
)

echo.
echo Press any key to exit...
pause >nul
