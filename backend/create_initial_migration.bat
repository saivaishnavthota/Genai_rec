@echo off
echo.
echo ================================================================================
echo                    Creating Initial Alembic Migration
echo ================================================================================
echo.

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo Activating virtual environment...
    if exist "venv\Scripts\activate.bat" (
        call venv\Scripts\activate.bat
    ) else (
        echo ERROR: Virtual environment not found!
        echo Please run: python -m venv venv
        pause
        exit /b 1
    )
)

echo.
echo Step 1: Creating initial migration...
python -m alembic revision --autogenerate -m "Initial migration - all tables"

if errorlevel 1 (
    echo.
    echo ERROR: Failed to create migration!
    pause
    exit /b 1
)

echo.
echo ✅ Initial migration created successfully!
echo.
echo Step 2: Review the migration file in alembic/versions/
echo.
echo Step 3: Apply the migration to your database:
echo    python -m alembic upgrade head
echo.
echo ⚠️  NOTE: Make sure your database is running and .env is configured correctly!
echo.
pause

