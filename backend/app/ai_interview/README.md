# AI Interview Proctor Module

Production-grade AI-led interview proctoring system integrated into the GenAI Hiring System.

## Overview

This module provides:
- **AI-led interviews**: Candidates interact via React app with AI interviewer
- **Real-time proctoring**: Head pose, face detection, phone detection, multi-speaker audio
- **ASR transcription**: Whisper-based automatic speech recognition
- **RAG-based scoring**: Hybrid retrieval (BM25 + vector) with Ollama LLM scoring
- **Flag tracking**: Debounced violation detection with 6-10s clip generation
- **Structured reports**: Citations, criteria scores, and recommendations

## Architecture

```
backend/app/ai_interview/
├── models/          # SQLAlchemy models (sessions, flags, KB docs)
├── schemas/         # Pydantic validation schemas
├── services/        # Business logic (interview, proctor, ASR, RAG, storage, clips)
├── routers/         # FastAPI endpoints
├── workers/         # Background workers (proctor, scoring)
└── utils/           # Utilities (flag tracker, timecode, security)
```

## Setup

### 1. Environment Variables

Add to `.env`:

```bash
# MinIO/S3 Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
S3_BUCKET=interview-blobs
S3_USE_SSL=false

# Ollama (for RAG scoring)
OLLAMA_API_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:3b-instruct

# Feature Flags
ENABLE_DIARIZATION=false
ENABLE_OCR=false

# Policy & Rubric Versions
POLICY_VERSION=1.0
RUBRIC_VERSION=1.0
```

### 2. Database Migrations

Run Alembic migration to create tables:

```bash
cd backend
alembic upgrade head
```

This creates:
- `ai_interview_sessions` - Interview sessions
- `ai_proctor_flags` - Proctoring violation flags
- `kb_docs` - Knowledge base documents (for RAG)

And enables PostgreSQL extensions:
- `uuid-ossp` - UUID generation
- `vector` - pgvector for embeddings
- `pg_trgm` - Full-text search

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Key dependencies:
- `faster-whisper` - ASR transcription
- `pgvector` - Vector similarity search
- `minio` - S3-compatible storage
- `opencv-python` - Face detection
- `onnxruntime` - Optional: YOLO phone detection

### 4. Setup MinIO (Local Development)

```bash
# Using Docker
docker run -p 9000:9000 -p 9001:9001 \
  minio/minio server /data --console-address ":9001"

# Access MinIO console: http://localhost:9001
# Default credentials: minioadmin / minioadmin
```

### 5. Seed Knowledge Base

Create a script `backend/seed_kb.py`:

```python
from app.database import SessionLocal
from app.ai_interview.models.kb_docs import KBDocument, KBBucket
from app.ai_interview.services.rag_service import RAGService

db = SessionLocal()
rag = RAGService()

# Add rubric documents
doc = KBDocument(
    role="software_engineer",
    level="senior",
    topic="system_design",
    bucket=KBBucket.RUBRIC,
    version="1.0",
    text="Senior engineers should demonstrate expertise in..."
)
db.add(doc)
db.commit()

# Generate embeddings (requires embedding model)
# await rag._get_embedding(doc.text)
```

Run: `python backend/seed_kb.py`

## API Endpoints

### Session Management

- `POST /api/ai-interview/start` - Start interview session
- `POST /api/ai-interview/{session_id}/end` - End session (idempotent)
- `GET /api/ai-interview/{session_id}/report` - Get full report

### Streaming

- `WS /api/ai-interview/{session_id}/stream` - WebSocket for audio/frames
- `POST /api/ai-interview/{session_id}/events` - Submit client telemetry

### Proctoring

- `GET /api/ai-interview/{session_id}/flags` - Get all flags

### Scoring

- `POST /api/ai-interview/{session_id}/score` - Trigger scoring (HR/Admin)

### Knowledge Base

- `POST /api/ai-interview/kb/ingest` - Ingest document (Admin)
- `GET /api/ai-interview/kb/search` - Search KB (HR/Admin)

### Review

- `POST /api/ai-interview/review/{session_id}/decision` - Set HR decision

## Flag Tracking Logic

### Head Turn
- **Moderate**: |yaw| > 35° for ≥ 2.0s
- **High**: |yaw| ≥ 45° for ≥ 3.0s

### Face Absent
- **Moderate**: ≥ 3s
- **High**: ≥ 8s

### Multi-Face
- **High**: > 1 face for ≥ 0.5s

### Phone Detection
- **Moderate**: conf ≥ 0.60 for ≥ 1.0s
- **High**: conf ≥ 0.75 for ≥ 2.0s

### Audio Multi-Speaker
- **Moderate**: ≥ 2s
- **High**: ≥ 5s

All flags include 2s pre/post padding for clip generation.

## Recommendation Policy

- **Auto-PASS**: final_score ≥ 7.0 AND no HIGH flags AND ≤ 2 MODERATE flags
- **Auto-FAIL**: ≥ 2 HIGH flags OR explicit policy breach
- **Else**: REVIEW

## Testing

Run tests:

```bash
cd backend
pytest tests/test_ai_flags.py
pytest tests/test_rag_retrieval.py
pytest tests/test_scoring_schema.py
pytest tests/test_api_contracts.py
```

## Local Development

### Start Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run Workers (Optional)

```python
from app.ai_interview.workers import ProctorWorker, ScoringWorker

# Start proctor worker
proctor = ProctorWorker()
await proctor.start()

# Start scoring worker
scorer = ScoringWorker()
await scorer.score_session(session_id=1)
```

## Production Deployment

### GPU Support (Optional)

For faster Whisper transcription and YOLO detection:

```bash
# Install CUDA-enabled packages
pip install faster-whisper[gpu]
pip install onnxruntime-gpu
```

Set in `.env`:
```bash
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16
```

### Monitoring

Health endpoints:
- `/healthz` - Liveness probe
- `/readyz` - Readiness probe (checks DB)

Metrics (Prometheus):
- `flags_emitted_total` - Total flags emitted
- `asr_latency_ms` - ASR processing latency
- `rag_latency_ms` - RAG scoring latency

## Notes

- **CPU Fallback**: All services work on CPU with lower FPS/frame sampling
- **WebRTC**: Token-based authentication; can fallback to frame uploads
- **Idempotency**: `/end` and `/score` endpoints are idempotent
- **Citations**: All AI decisions include citations for audit

## Integration with Existing Flow

After AI interview completion:
- If `recommendation == PASS`: Trigger human interview scheduling
- If `recommendation == REVIEW`: Send to HR dashboard
- If `recommendation == FAIL`: Send rejection email

## Troubleshooting

### MinIO Connection Error
- Check `MINIO_ENDPOINT` matches your MinIO server
- Ensure MinIO is running: `docker ps | grep minio`

### Whisper Model Not Found
- Models auto-download on first use
- For faster startup, pre-download: `python -c "from faster_whisper import WhisperModel; WhisperModel('base')"`

### pgvector Extension Error
- Ensure PostgreSQL has `vector` extension: `CREATE EXTENSION vector;`
- Check migration ran successfully: `alembic current`

### Ollama Connection Error
- Check `OLLAMA_API_URL` is correct
- Test: `curl http://ollama:11434/api/tags`

## License

Part of GenAI Hiring System.

