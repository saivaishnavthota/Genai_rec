@echo off
title GenAI Backend Server
cd backend

echo.
echo ================================================================================
echo                          🚀 Starting Backend Server
echo ================================================================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        echo 💡 Make sure Python is installed and in PATH
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo 📦 Installing dependencies...
pip install -q --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  .env file not found in backend directory
    echo.
    echo 📝 Creating .env file from template...
    if exist "..\env.example" (
        copy ..\env.example .env >nul
        echo ✅ .env file created from env.example
    ) else (
        echo ❌ env.example not found. Please create .env manually.
        echo.
        echo 💡 Create .env file with:
        echo    DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/genai_hiring
        echo    POSTGRES_USER=postgres
        echo    POSTGRES_PASSWORD=YOUR_PASSWORD
        echo.
        pause
        exit /b 1
    )
    echo.
    echo ⚠️  IMPORTANT: Edit .env file and update PostgreSQL password if needed!
    echo 💡 Default password is 'vaishnav'
    echo.
    timeout /t 3 /nobreak >nul
)

REM Test database connection before starting
echo 🔍 Testing database connection...
python test_db_connection.py
if errorlevel 1 (
    echo.
    echo ❌ Database connection test failed!
    echo 💡 Please fix the database connection before starting the server
    echo 📚 See FIX_DATABASE_CONNECTION.md for help
    echo.
    pause
    exit /b 1
)
echo.

REM Run the server
echo.
echo 🚀 Starting FastAPI server...
echo    Backend URL: http://localhost:8000
echo    API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause

