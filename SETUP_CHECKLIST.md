# Setup Checklist

## ✅ Prerequisites Installation

- [ ] **Python 3.11+** installed
  - Check: `python --version`
  - Download: https://www.python.org/downloads/

- [ ] **Node.js 18+** installed
  - Check: `node --version`
  - Download: https://nodejs.org/

- [ ] **PostgreSQL 15+** installed OR Docker available
  - Check: `psql --version` OR `docker --version`

- [ ] **Redis 7+** installed OR Docker available
  - Check: `redis-cli --version` OR `docker --version`

- [ ] **Ollama** installed (for AI features)
  - Check: `ollama --version`
  - Download: https://ollama.ai/download
  - **Important**: Ollama runs locally, NOT in Docker

## ✅ Environment Setup

- [ ] Copy `env.example` to `.env`
  ```bash
  copy env.example .env
  ```

- [ ] Update `.env` file with your settings:
  - [ ] Database credentials
  - [ ] Redis connection
  - [ ] Email/SMTP settings
  - [ ] Secret keys (SECRET_KEY, JWT_SECRET_KEY)

## ✅ Ollama Setup

- [ ] Ollama is installed
- [ ] Ollama is running
  - Windows: Should run automatically as service
  - macOS/Linux: Run `ollama serve`
- [ ] Required model is downloaded
  ```bash
  ollama pull qwen2.5:3b-instruct
  ```
- [ ] Verify Ollama works
  ```bash
  curl http://localhost:11434/api/version
  ```

## ✅ Database Setup

- [ ] PostgreSQL is running
- [ ] Database `genai_hiring` is created
  ```sql
  CREATE DATABASE genai_hiring;
  ```
- [ ] Database connection works (check .env DATABASE_URL)

## ✅ Redis Setup

- [ ] Redis is running
- [ ] Test connection: `redis-cli ping` (should return PONG)

## ✅ Backend Setup

- [ ] Navigate to backend: `cd backend`
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate virtual environment:
  - Windows: `venv\Scripts\activate`
  - macOS/Linux: `source venv/bin/activate`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Initialize database: `python init_db.py`
- [ ] Backend runs successfully: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- [ ] Verify backend: http://localhost:8000/health

## ✅ Frontend Setup

- [ ] Navigate to frontend: `cd frontend`
- [ ] Install dependencies: `npm install`
- [ ] Frontend runs successfully: `npm start`
- [ ] Verify frontend: http://localhost:3000

## ✅ Final Verification

- [ ] Backend API is accessible: http://localhost:8000/health
- [ ] Frontend is accessible: http://localhost:3000
- [ ] API documentation works: http://localhost:8000/docs
- [ ] Ollama is responding: `curl http://localhost:11434/api/version`
- [ ] Can log in to the application

## 🚀 Quick Start Commands

### Option 1: Use Scripts (Windows)
```bash
# Terminal 1
start-backend.bat

# Terminal 2
start-frontend.bat
```

### Option 2: Manual Commands
```bash
# Terminal 1 - Backend
cd backend
venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend
cd frontend
npm start
```

## 📚 Additional Resources

- **Detailed Setup**: [MANUAL_SETUP.md](MANUAL_SETUP.md)
- **Quick Start**: [QUICK_START.md](QUICK_START.md)
- **Troubleshooting**: See MANUAL_SETUP.md Troubleshooting section

