# Quick Start Guide - AI Interview System

## ✅ Setup Complete!

Your application is now running:

- **Frontend**: http://localhost:3000 (✅ Running)
- **Backend**: http://localhost:8000 (Starting...)
- **API Docs**: http://localhost:8000/docs

## Next Steps

### 1. Access the Application

Open your browser and navigate to:
```
http://localhost:3000
```

### 2. Login to the System

Use your existing credentials to login to the GenAI Hiring System.

### 3. Start an AI Interview

1. Navigate to an application (from the Applications page)
2. Look for the "Start AI Interview" button or option
3. Click to start a new AI interview session

### 4. Test the Interview Flow

**Candidate View** (`/ai-interview/:sessionId`):
- Pre-check: Test microphone and camera
- Consent: Accept monitoring consent
- Calibration: Align head pose
- Interview: Answer questions while being monitored

**HR Review View** (`/review/ai-interview/:sessionId`):
- View video recording with flag markers
- Review scorecard with per-criterion scores
- Read transcript with question sections
- See all proctoring flags (head-turn, face-absent, etc.)

## Troubleshooting

### Backend Not Starting?

1. Check if port 8000 is already in use:
   ```powershell
   netstat -ano | findstr :8000
   ```

2. Check backend logs in the terminal window

3. Verify database connection:
   ```powershell
   cd backend
   python test_db_connection.py
   ```

### Frontend Not Loading?

1. Check if port 3000 is already in use:
   ```powershell
   netstat -ano | findstr :3000
   ```

2. Check frontend logs in the terminal window

3. Try clearing browser cache and reloading

### Database Issues?

1. Run the extensions setup:
   ```powershell
   cd backend
   python setup-extensions.py
   ```

2. Run migrations:
   ```powershell
   cd backend
   alembic upgrade head
   ```

## Stopping Services

To stop the services, close the terminal windows that are running:
- Backend Server
- Frontend Server

Or use:
```powershell
# Find and kill processes
Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*node*"} | Stop-Process
```

## Restart Services

To restart everything, simply run:
```powershell
.\START_AI_INTERVIEW.bat
```

Or manually:
```powershell
# Backend
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (in another terminal)
cd frontend
npm start
```

## Need Help?

- Check `SETUP_AI_INTERVIEW.md` for detailed setup instructions
- Check `RUN_AI_INTERVIEW.md` for detailed usage instructions
- Check backend logs in `backend/logs/`
- Check frontend logs in the terminal
