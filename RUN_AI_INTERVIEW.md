# Quick Start - Running AI Interview System

## Step-by-Step Instructions

### Step 1: Install Dependencies

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### Step 2: Setup Database Extensions

**IMPORTANT:** Create PostgreSQL extensions BEFORE running migrations.

Connect to PostgreSQL (using psql, pgAdmin, or any SQL client) and run:

```sql
-- Required extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Optional: Full-text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Optional: Vector similarity (requires pgvector installation)
-- Skip this if you haven't installed pgvector yet
-- CREATE EXTENSION IF NOT EXISTS "vector";
```

**Or use the provided SQL file:**
```bash
psql -U postgres -d your_database -f backend/setup_extensions.sql
```

**Note:** The `vector` extension requires pgvector to be installed. See `INSTALL_PGVECTOR.md` for installation instructions. The system works without it (uses BM25 search only).

### Step 3: Run Migrations

```bash
cd backend
alembic upgrade head
```

### Step 4: Start MinIO (Object Storage)

**Using Docker:**
```bash
docker run -d -p 9000:9000 -p 9001:9001 \
  --name minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ":9001"
```

Verify: http://localhost:9001 (login: minioadmin/minioadmin)

### Step 5: Configure Environment

**Backend `.env`** (add these lines):
```bash
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
S3_BUCKET=interview-blobs
OLLAMA_API_URL=http://localhost:11434
POLICY_VERSION=1.0
RUBRIC_VERSION=1.0
```

**Frontend `.env`** (create if needed):
```bash
REACT_APP_API_URL=http://localhost:8000
```

### Step 6: Start Services

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### Step 7: Test the Interview

#### Option A: Via Frontend (Recommended)

1. **Login** to http://localhost:3000
2. **Create/Select Application** from HR dashboard
3. **Start AI Interview** - this creates a session
4. **Note the session_id** from URL or response

#### Option B: Via API (Quick Test)

1. **Get JWT Token:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"your-email\",\"password\":\"your-password\"}"
```

2. **Start Interview Session:**
```bash
curl -X POST http://localhost:8000/api/ai-interview/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "{\"application_id\":1,\"job_id\":1}"
```

3. **Copy the `session_id` from response**

### Step 8: Test Candidate Interface

1. Open: `http://localhost:3000/ai-interview/SESSION_ID`
   (Replace SESSION_ID with actual ID)

2. **Allow camera/microphone** when browser prompts

3. **Complete stages:**
   - ✅ Pre-check: Test devices → Click "Ready"
   - ✅ Consent: Read → Check boxes → "Start Interview"
   - ✅ Calibration: Position yourself → Wait for green → "Calibration Complete"
   - ✅ Live Interview: Interview runs → Watch for flags → "End Interview"
   - ✅ Completing: Wait for processing
   - ✅ Completed: Success message

### Step 9: Test HR Review

1. After interview completes, open:
   `http://localhost:3000/review/ai-interview/SESSION_ID`

2. **Review interface:**
   - Video player with flag markers
   - Scorecard tab (scores, criteria)
   - Transcript tab (click to seek)
   - Flags tab (all violations)

3. **Submit decision:**
   - Select PASS/REVIEW/FAIL
   - Add notes (optional)
   - Click "Submit Decision"

## Quick Verification

Check these URLs work:
- ✅ Backend: http://localhost:8000/healthz
- ✅ API Docs: http://localhost:8000/docs
- ✅ Frontend: http://localhost:3000
- ✅ MinIO: http://localhost:9001

## Troubleshooting

**"Module not found" errors:**
- Backend: `pip install -r requirements.txt`
- Frontend: `npm install`

**"Extension vector does not exist":**
```sql
CREATE EXTENSION vector;
```

**"MinIO connection refused":**
- Check Docker: `docker ps | grep minio`
- Restart: `docker restart minio`

**Camera not working:**
- Check browser permissions
- Try Chrome browser
- localhost works without HTTPS

**MediaPipe not loading:**
- Requires internet (loads from CDN)
- May take 10-20 seconds first time
- Check browser console for errors

## What to Look For

### During Interview:
- ✅ Camera feed visible
- ✅ Audio meter shows activity
- ✅ Head pose gauge updates (if MediaPipe loads)
- ✅ Timeline shows progress
- ✅ Flags appear as toasts if violations detected
- ✅ Network indicator shows connection status

### During Review:
- ✅ Video player loads
- ✅ Flag markers on timeline
- ✅ Scorecard shows scores
- ✅ Transcript is readable
- ✅ Flags table populated
- ✅ Decision submission works

## Next Steps

1. Seed knowledge base with rubrics
2. Test with longer interviews
3. Customize UI/styling
4. Add more test scenarios

## Need Help?

- Check browser console (F12) for errors
- Check backend terminal for logs
- Review SETUP_AI_INTERVIEW.md for detailed guide
- Review QUICK_TEST_AI_INTERVIEW.md for quick fixes

