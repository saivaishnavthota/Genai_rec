# Manual Setup Guide - Run Backend and Frontend Locally

This guide will help you run the GenAI Hiring System manually without Docker, or with only PostgreSQL/Redis in Docker.

## Prerequisites

### Required Software
1. **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download Node.js](https://nodejs.org/)
3. **PostgreSQL 15+** - [Download PostgreSQL](https://www.postgresql.org/download/) OR use Docker for DB
4. **Redis 7+** - [Download Redis](https://redis.io/download) OR use Docker for Redis
5. **Ollama** - [Download Ollama](https://ollama.ai/download) (for AI features)

### Optional: Docker for Database Only
If you prefer to run only PostgreSQL and Redis in Docker, you can use:
```bash
docker-compose up postgres redis
```

## Step 1: Setup Ollama (Run Locally)

### Install Ollama
1. Download and install Ollama from https://ollama.ai/download
2. Start Ollama service:
   - **Windows**: Ollama runs as a service automatically after installation
   - **macOS/Linux**: Run `ollama serve` in terminal

### Pull Required Model
```bash
ollama pull qwen2.5:3b-instruct
```

### Verify Ollama is Running
```bash
# Test Ollama API
curl http://localhost:11434/api/version

# Should return version information
```

## Step 2: Setup Environment Variables

1. Copy the environment example file:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` file and update these values:
   ```env
   # Database (if running locally, not in Docker)
   DATABASE_URL=postgresql://postgres:vaishnav@localhost:5432/genai_hiring
   REDIS_URL=redis://localhost:6379
   
   # Ollama (running locally)
   OLLAMA_HOST=localhost
   OLLAMA_PORT=11434
   
   # Frontend URL
   FRONTEND_URL=http://localhost:3000
   
   # API URL
   API_BASE_URL=http://localhost:8000
   REACT_APP_API_URL=http://localhost:8000
   ```

## Step 3: Setup Backend

### Navigate to Backend Directory
```bash
cd backend
```

### Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Initialize Database
```bash
# Create database tables
python init_db.py

# Or run directly
python -c "from app.database import create_tables; create_tables()"
```

### Run Backend Server
```bash
# Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or using Python
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend should now be running at: **http://localhost:8000**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Step 4: Setup Frontend

### Open New Terminal Window
Keep the backend running and open a new terminal.

### Navigate to Frontend Directory
```bash
cd frontend
```

### Install Dependencies
```bash
npm install
```

### Run Frontend Development Server
```bash
npm start
```

Frontend should now be running at: **http://localhost:3000**

## Step 5: Verify Everything Works

1. **Check Backend**: http://localhost:8000/health
2. **Check Frontend**: http://localhost:3000
3. **Check API Docs**: http://localhost:8000/docs
4. **Check Ollama**: `curl http://localhost:11434/api/version`

## Quick Start Commands Summary

### Terminal 1 - Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2 - Frontend
```bash
cd frontend
npm install
npm start
```

### Terminal 3 - Database (if using Docker for DB only)
```bash
docker-compose up postgres redis
```

## Troubleshooting

### Backend Issues

**Import Errors:**
```bash
# Make sure you're in the backend directory
cd backend
# Activate virtual environment
venv\Scripts\activate  # Windows
```

**Database Connection Error:**
- Check PostgreSQL is running
- Verify DATABASE_URL in .env file
- Check if database exists: `psql -U postgres -c "CREATE DATABASE genai_hiring;"`

**Redis Connection Error:**
- Check Redis is running: `redis-cli ping`
- Should return: `PONG`
- If using Docker: `docker-compose up redis`

**Ollama Connection Error:**
- Check Ollama is running: `curl http://localhost:11434/api/version`
- If not running, start it: `ollama serve`
- Verify model is installed: `ollama list`

### Frontend Issues

**Port Already in Use:**
```bash
# Kill process on port 3000
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:3000 | xargs kill -9
```

**Module Not Found:**
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**API Connection Error:**
- Verify backend is running on http://localhost:8000
- Check REACT_APP_API_URL in .env file
- Make sure CORS is configured correctly

## Environment-Specific Notes

### Windows
- Use `venv\Scripts\activate` to activate virtual environment
- Use `python` instead of `python3`
- Ollama runs as a Windows service automatically

### macOS/Linux
- Use `source venv/bin/activate` to activate virtual environment
- Use `python3` instead of `python`
- You may need to run `ollama serve` manually

## Optional: Using Docker for Database Only

If you want to run PostgreSQL and Redis in Docker but everything else locally:

1. Start only database services:
   ```bash
   docker-compose up postgres redis
   ```

2. In your `.env` file, use Docker service names:
   ```env
   # When backend runs locally but DB in Docker
   DATABASE_URL=postgresql://postgres:vaishnav@localhost:5432/genai_hiring
   REDIS_URL=redis://localhost:6379
   ```

3. Run backend and frontend manually as described above.

## Development Tips

- **Hot Reload**: Both backend (with --reload) and frontend (default) support hot reload
- **Logs**: Check terminal output for errors
- **API Testing**: Use http://localhost:8000/docs for interactive API testing
- **Database GUI**: Consider using pgAdmin or DBeaver for database management

