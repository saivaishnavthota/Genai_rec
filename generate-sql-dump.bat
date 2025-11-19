@echo off
setlocal enabledelayedexpansion
title GenAI PostgreSQL SQL Dump Generator

echo.
echo ================================================================================
echo                      📄 GenAI PostgreSQL SQL Dump Generator
echo ================================================================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Check if PostgreSQL container is running
docker-compose ps postgres | findstr "Up" >nul 2>&1
if errorlevel 1 (
    echo ❌ PostgreSQL container is not running
    echo 💡 Start the system first: start.bat
    pause
    exit /b 1
)

echo ✅ PostgreSQL container is running

REM Create database directory if it doesn't exist
if not exist "database" mkdir database

REM Generate timestamp for filename
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set mydate=%%c-%%a-%%b
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set mytime=%%a%%b
set mytime=!mytime: =!
set timestamp=!mydate!_!mytime!

echo.
echo 🎯 SQL Dump Options:
echo    1. Complete database dump (structure + data)
echo    2. Structure only (schema)
echo    3. Data only (inserts)
echo    4. Custom tables only
echo.
set /p choice=Select dump type (1-4): 

if "!choice!"=="1" (
    set dump_file=database\genai_hiring_complete_!timestamp!.sql
    set dump_args=--clean --if-exists --create --verbose
    set dump_desc=Complete database dump
) else if "!choice!"=="2" (
    set dump_file=database\genai_hiring_schema_!timestamp!.sql
    set dump_args=--schema-only --clean --if-exists --create --verbose
    set dump_desc=Schema only dump
) else if "!choice!"=="3" (
    set dump_file=database\genai_hiring_data_!timestamp!.sql
    set dump_args=--data-only --verbose
    set dump_desc=Data only dump
) else if "!choice!"=="4" (
    set dump_file=database\genai_hiring_custom_!timestamp!.sql
    echo.
    echo Available tables:
    docker-compose exec -T postgres psql -U postgres -d genai_hiring -c "\dt"
    echo.
    set /p tables=Enter table names (space-separated): 
    set dump_args=--verbose
    for %%t in (!tables!) do set dump_args=!dump_args! -t %%t
    set dump_desc=Custom tables dump
) else (
    echo ❌ Invalid choice
    pause
    exit /b 1
)

echo.
echo 🔄 Generating !dump_desc!...
echo 📁 Output file: !dump_file!
echo.

REM Execute pg_dump
docker-compose exec -T postgres pg_dump -U postgres -d genai_hiring !dump_args! > "!dump_file!"

if errorlevel 1 (
    echo ❌ SQL dump generation failed!
    if exist "!dump_file!" del "!dump_file!"
    pause
    exit /b 1
) else (
    echo ✅ SQL dump generated successfully!
    
    REM Get file size
    for %%A in ("!dump_file!") do set size=%%~zA
    echo 📊 File size: !size! bytes
    
    REM Count lines
    for /f %%C in ('find /v /c "" ^< "!dump_file!"') do set lines=%%C
    echo 📄 Total lines: !lines!
)

echo.
echo 📋 Dump Information:
echo    📁 File: !dump_file!
echo    📊 Type: !dump_desc!
echo    📅 Created: !timestamp!
echo.

echo 🎯 Next Actions:
echo    1. View SQL dump file
echo    2. Copy to another location
echo    3. Compress the file
echo    4. Exit
echo.
set /p action=Select action (1-4): 

if "!action!"=="1" (
    echo.
    echo 📄 Opening SQL dump file...
    notepad "!dump_file!"
) else if "!action!"=="2" (
    echo.
    set /p dest=Enter destination path: 
    copy "!dump_file!" "!dest!" >nul
    if errorlevel 1 (
        echo ❌ Copy failed!
    ) else (
        echo ✅ File copied to !dest!
    )
) else if "!action!"=="3" (
    echo.
    echo 🗜️ Compressing SQL dump...
    powershell -Command "Compress-Archive -Path '!dump_file!' -DestinationPath '!dump_file!.zip'"
    if errorlevel 1 (
        echo ❌ Compression failed!
    ) else (
        echo ✅ Compressed file created: !dump_file!.zip
        for %%A in ("!dump_file!.zip") do set zipsize=%%~zA
        echo 📊 Compressed size: !zipsize! bytes
    )
)

echo.
echo 🎉 SQL dump generation completed!
echo.
echo Press any key to exit...
pause >nul
