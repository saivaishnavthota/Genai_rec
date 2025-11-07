# AI Interview Proctoring - Setup & Testing Guide

## Prerequisites

- Node.js 16+ and npm
- Python 3.8+ and pip
- PostgreSQL database
- Redis (optional, for caching)
- MinIO (for file storage - can use Docker)

## Step 1: Backend Setup

### 1.1 Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `faster-whisper` - ASR transcription
- `pgvector` - Vector similarity search
- `minio` - S3-compatible storage
- `opencv-python` - Face detection
- `numpy`, `structlog`, `prometheus-client` - Other dependencies

**Note:** If you encounter issues:
- On Windows: You may need Visual C++ Build Tools for some packages
- GPU support: Install `faster-whisper[gpu]` and `onnxruntime-gpu` if you have CUDA

### 1.2 Setup PostgreSQL Extensions

Connect to your PostgreSQL database and run:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

### 1.3 Run Database Migrations

```bash
cd backend
alembic upgrade head
```

This creates the AI interview tables:
- `ai_interview_sessions`
- `ai_proctor_flags`
- `kb_docs`

### 1.4 Setup MinIO (Object Storage)

**Option A: Using Docker (Recommended)**

```bash
docker run -d -p 9000:9000 -p 9001:9001 \
  --name minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ":9001"
```

Access MinIO Console: http://localhost:9001
- Username: `minioadmin`
- Password: `minioadmin`

**Option B: Local Installation**

Download from https://min.io/download

### 1.5 Configure Environment Variables

Create/update `backend/.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/genai_hiring

# Redis
REDIS_URL=redis://localhost:6379

# MinIO/S3
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
S3_BUCKET=interview-blobs
S3_USE_SSL=false

# Ollama (for RAG scoring)
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b-instruct

# Feature Flags
ENABLE_DIARIZATION=false
ENABLE_OCR=false

# Policy & Rubric Versions
POLICY_VERSION=1.0
RUBRIC_VERSION=1.0
```

### 1.6 Seed Knowledge Base (Optional)

Create a script `backend/seed_kb.py`:

```python
from app.database import SessionLocal
from app.ai_interview.models.kb_docs import KBDocument, KBBucket

db = SessionLocal()

# Add sample rubric
doc = KBDocument(
    role="software_engineer",
    level="senior",
    topic="system_design",
    bucket=KBBucket.RUBRIC,
    version="1.0",
    text="Senior software engineers should demonstrate deep understanding of distributed systems, scalability patterns, and system architecture. Key evaluation criteria: 1) Technical knowledge (0-10), 2) Problem-solving ability (0-10), 3) Communication skills (0-10)."
)

db.add(doc)
db.commit()
db.close()
```

Run: `python backend/seed_kb.py`

### 1.7 Start Backend Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use your existing startup script:
```bash
python -m uvicorn app.main:app --reload
```

Verify backend is running:
- Health check: http://localhost:8000/healthz
- API docs: http://localhost:8000/docs

## Step 2: Frontend Setup

### 2.1 Install Frontend Dependencies

```bash
cd frontend
npm install
```

This installs:
- `@mediapipe/tasks-vision` - Face detection and head pose tracking
- All existing React dependencies

**Note:** If you encounter peer dependency warnings, they're usually safe to ignore.

### 2.2 Configure Environment Variables

Create/update `frontend/.env`:

```bash
REACT_APP_API_URL=http://localhost:8000
```

### 2.3 Start Frontend Development Server

```bash
cd frontend
npm start
```

The app will open at http://localhost:3000

## Step 3: Testing the Interview Process

### 3.1 Create a Test Session

**Option A: Via API (Recommended for testing)**

```bash
# First, get a JWT token (login as HR/Admin)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com", "password": "your-password"}'

# Start an AI interview session
curl -X POST http://localhost:8000/api/ai-interview/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "application_id": 1,
    "job_id": 1
  }'
```

Response will include `session_id` (e.g., `{"session_id": 123, ...}`)

**Option B: Via Frontend**

1. Navigate to http://localhost:3000
2. Login as HR/Admin
3. Create a job and application (if not exists)
4. Start interview from application details page

### 3.2 Test Candidate Interview Flow

1. **Navigate to Interview Room:**
   ```
   http://localhost:3000/ai-interview/123
   ```
   (Replace `123` with your actual session_id)

2. **Pre-check Stage:**
   - Allow camera/microphone permissions when prompted
   - Select camera and microphone devices
   - Click "Test Camera & Mic"
   - Verify video preview appears
   - Click "Ready" when devices are working

3. **Consent Stage:**
   - Read the consent banner
   - Check both checkboxes
   - Click "Start Interview"

4. **Calibration Stage:**
   - Position yourself in front of camera
   - Look straight ahead
   - Wait for head pose gauge to show "Aligned" (green)
   - Click "Calibration Complete"

5. **Live Interview Stage:**
   - Interview begins
   - Watch for:
     - Video preview showing your feed
     - Live timeline with flag markers (if any flags detected)
     - Audio meter showing audio levels
     - Network indicator showing connection status
   - Head pose tracking runs automatically
   - Flags appear as toast notifications if violations detected

6. **End Interview:**
   - Click "End Interview" button
   - Wait for "Finalizing Interview" screen
   - Redirects to completion page

### 3.3 Test HR Review Flow

1. **Navigate to Review Page:**
   ```
   http://localhost:3000/review/ai-interview/123
   ```
   (Replace `123` with your session_id)

2. **Review Interface:**
   - **Video Player**: Shows interview recording with flag markers
   - **Scorecard Tab**: Overall score, criteria breakdown, citations
   - **Transcript Tab**: Time-stamped transcript (click to seek)
   - **Flags Tab**: Table of all proctoring flags

3. **Make Decision:**
   - Select PASS, REVIEW, or FAIL
   - Add optional notes
   - Click "Submit Decision"

## Step 4: Common Issues & Troubleshooting

### Backend Issues

**Issue: `pgvector` extension not found**
```sql
-- Install pgvector extension
CREATE EXTENSION vector;
```

**Issue: MinIO connection error**
- Check MinIO is running: `docker ps | grep minio`
- Verify `MINIO_ENDPOINT` in `.env` matches your setup
- Check firewall/network settings

**Issue: Whisper model not found**
- Models auto-download on first use
- Check internet connection
- For faster startup, pre-download:
  ```python
  from faster_whisper import WhisperModel
  model = WhisperModel("base")
  ```

**Issue: MediaPipe not loading in browser**
- Check browser console for errors
- Verify `@mediapipe/tasks-vision` is installed
- Models load from CDN (requires internet)

### Frontend Issues

**Issue: Camera/microphone not working**
- Check browser permissions (Settings → Privacy → Camera/Microphone)
- Ensure HTTPS in production (required for getUserMedia)
- Try different browser (Chrome recommended)
- Check device manager for hardware issues

**Issue: WebRTC connection fails**
- Check backend WebSocket endpoint is accessible
- Verify CORS settings in backend
- Check firewall/network settings
- Falls back to WebSocket automatically

**Issue: Flags not appearing**
- Check browser console for errors
- Verify backend flags endpoint: `GET /api/ai-interview/:id/flags`
- Check network tab for API calls
- Flags poll every 2 seconds by default

**Issue: TypeScript errors**
- Run `npm install` to ensure all types are installed
- Check `tsconfig.json` exists (may need to create)
- TypeScript is optional - JS files will work too

### Database Issues

**Issue: Migration fails**
```bash
# Check current migration status
alembic current

# Check migration history
alembic history

# If stuck, you may need to manually fix the database
```

**Issue: Missing tables**
```bash
# Re-run migrations
alembic upgrade head

# Or manually create tables using SQL
```

## Step 5: Development Tips

### Backend Development

1. **Enable Debug Logging:**
   ```python
   # In config.py
   debug = True
   ```

2. **Test API Endpoints:**
   - Use http://localhost:8000/docs for interactive API docs
   - Test endpoints directly with curl/Postman

3. **Monitor Logs:**
   ```bash
   # Backend logs appear in console
   # Check for errors, warnings
   ```

### Frontend Development

1. **Browser DevTools:**
   - Open DevTools (F12)
   - Check Console for errors
   - Monitor Network tab for API calls
   - Check Application tab for localStorage

2. **Hot Reload:**
   - React app auto-reloads on file changes
   - Backend needs manual restart for Python changes

3. **Test Different Scenarios:**
   - Test with different browsers
   - Test with/without camera
   - Test network interruptions
   - Test permission denials

## Step 6: Production Checklist

Before deploying to production:

- [ ] Set `DEBUG=false` in backend
- [ ] Use production database (not localhost)
- [ ] Configure MinIO/S3 with proper credentials
- [ ] Set up HTTPS (required for getUserMedia)
- [ ] Configure CORS properly
- [ ] Set up proper logging
- [ ] Load test the system
- [ ] Test on different devices/browsers
- [ ] Set up monitoring/alerting
- [ ] Configure backup for database
- [ ] Set up CDN for MediaPipe models (optional)

## Quick Start Commands

```bash
# Terminal 1: Start Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Frontend
cd frontend
npm start

# Terminal 3: Start MinIO (if using Docker)
docker run -d -p 9000:9000 -p 9001:9001 \
  --name minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ":9001"
```

## Next Steps

1. **Customize Interview Flow:**
   - Adjust question count
   - Modify calibration duration
   - Customize UI styling

2. **Add More Features:**
   - Screen sharing detection
   - Background noise detection
   - Real-time AI feedback

3. **Integrate with Existing Flow:**
   - Link to application workflow
   - Send notifications
   - Update application status

## Support

If you encounter issues:
1. Check logs (backend console, browser console)
2. Verify all services are running
3. Check environment variables
4. Review this guide for common issues
5. Check API documentation at `/docs`

