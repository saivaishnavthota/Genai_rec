# AI Interview Data Flow & Evaluation System

## 📊 Complete Data Flow Overview

### 1. **During the Interview - Data Collection**

#### What Data is Collected:
- **Video Recording**: Raw video stream from candidate's webcam (stored in MinIO/S3)
- **Audio Recording**: Audio stream transcribed to text
- **Proctoring Flags**: Real-time violations detected
  - Head turns (yaw > 35° for 2+ seconds)
  - Face absent (face not visible for 3+ seconds)
  - Multiple faces detected
  - Phone detection (if enabled)
  - Audio multi-speaker detection
- **Client Telemetry**: Head pose data, face detection confidence, timestamps
- **Transcript**: Speech-to-text conversion using Whisper ASR

#### Where Data is Stored:
```
Database (PostgreSQL):
├── ai_interview_sessions
│   ├── session metadata (id, application_id, job_id, status)
│   ├── started_at, ended_at timestamps
│   ├── total_score (0.00-10.00)
│   ├── recommendation (PASS/REVIEW/FAIL)
│   ├── transcript_url (pointer to storage)
│   └── report_json (full scoring report with citations)
│
└── ai_proctor_flags
    ├── flag_type (head_turn, face_absent, multi_face, etc.)
    ├── severity (low, moderate, high)
    ├── confidence (0.0000-1.0000)
    ├── t_start, t_end (timestamps in seconds)
    ├── clip_url (6-10s video clip of violation)
    └── flag_metadata (additional context)

Object Storage (MinIO/S3):
├── /recordings/{session_id}/raw.mp4 (full video)
├── /recordings/{session_id}/transcript.json (transcript)
└── /recordings/{session_id}/clips/{flag_id}.mp4 (violation clips)
```

---

## 🧮 Evaluation Process

### Step 1: Interview Completion
When candidate clicks "End Interview":
1. Session status changes: `LIVE` → `FINALIZING`
2. Video/audio recording stops
3. Transcript is finalized using Whisper ASR

### Step 2: Scoring (RAG-Based Evaluation)

**Trigger**: HR/Admin manually triggers scoring via `/api/ai-interview/{session_id}/score` endpoint

**Process**:
1. **Transcript Retrieval**: Loads transcript from storage
2. **RAG-Based Scoring**:
   - Uses **Hybrid Retrieval** (BM25 + Vector search) to find relevant knowledge base documents
   - Retrieves job-specific criteria, rubrics, and evaluation guidelines
   - Sends transcript + context to **Ollama LLM** (qwen2.5:3b-instruct) for scoring
3. **Scoring Output**:
   ```json
   {
     "criteria": [
       {
         "criterion_name": "Technical Skills",
         "score": 8.5,
         "explanation": "Candidate demonstrated strong understanding...",
         "citations": [{"doc_id": 123, "excerpt": "..."}]
       },
       {
         "criterion_name": "Communication",
         "score": 7.2,
         "explanation": "...",
         "citations": []
       }
     ],
     "final_score": 7.85,
     "summary": "Overall assessment...",
     "improvement_tip": "Consider practicing more..."
   }
   ```
4. **Recommendation Calculation**:
   - Based on `total_score` and flag severity
   - Logic: `calculate_recommendation()` in `InterviewService`
   - Returns: `PASS`, `REVIEW`, or `FAIL`

### Step 3: Data Storage
- `total_score` saved to `ai_interview_sessions.total_score`
- Full scoring report saved to `ai_interview_sessions.report_json`
- `recommendation` saved to `ai_interview_sessions.recommendation`

---

## 👥 Who Can See the Evaluation

### 1. **HR & Admin Users**
**Access Level**: Full access to all interview data

**What They Can See**:
- ✅ Complete interview report (`/review/ai-interview/{session_id}`)
- ✅ Video recording with flag markers
- ✅ Full transcript
- ✅ Detailed scorecard with:
  - Criteria scores (0-10)
  - Explanations for each score
  - Citations from knowledge base
  - Final overall score
  - Improvement tips
- ✅ All proctoring flags with severity
- ✅ Flag video clips (6-10s violations)
- ✅ AI recommendation (PASS/REVIEW/FAIL)

**What They Can Do**:
- Trigger scoring manually (`POST /api/ai-interview/{session_id}/score`)
- View reports (`GET /api/ai-interview/{session_id}/report`)
- Set final HR decision (`POST /api/ai-interview/review/{session_id}/decision`)
  - Override AI recommendation
  - Add review notes
  - Final status: PASS, REVIEW, or FAIL

**Access Points**:
1. **HR Dashboard**: Application list → Application details → "Start AI Interview" button
2. **Review Page**: `/review/ai-interview/{session_id}` (after interview completed)
3. **Application Details**: Shows AI interview scores alongside other scores

### 2. **Candidates**
**Access Level**: Limited - can only view their own interview

**What They Can See** (if implemented):
- ✅ Their own interview report
- ✅ Their own transcript
- ✅ Their own scorecard
- ✅ Flags that were raised during their interview

**What They Cannot See**:
- ❌ Other candidates' interviews
- ❌ HR review notes
- ❌ Final HR decision (until notified)

**Access Control**:
```python
# In backend/app/ai_interview/routers/scoring.py
@router.get("/{session_id}/report")
async def get_report(...):
    # Candidate can view own session
    # HR/Admin can view any session
```

### 3. **Interviewers (Traditional Interviews)**
**Access Level**: None - AI interviews are separate from traditional interviews

**Note**: Traditional interview reviews are stored separately in `interview_reviews` table

---

## 🔍 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CANDIDATE INTERVIEW                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              REAL-TIME DATA COLLECTION                        │
│  • Video Stream → MinIO/S3 (raw.mp4)                        │
│  • Audio Stream → Whisper ASR → Transcript                  │
│  • Head Pose Events → Proctor Service → Flags               │
│  • Face Detection → Proctoring Flags                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   DATABASE STORAGE                           │
│  • ai_interview_sessions (metadata, status)                 │
│  • ai_proctor_flags (violations with timestamps)            │
│  • kb_docs (evaluation rubrics - for RAG)                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    SCORING PROCESS                           │
│  (Triggered by HR/Admin)                                     │
│                                                              │
│  1. Load Transcript from Storage                             │
│  2. RAG Retrieval:                                           │
│     - Hybrid Search (BM25 + Vector)                          │
│     - Find relevant KB documents                             │
│  3. LLM Scoring (Ollama):                                     │
│     - Transcript + Context → LLM                                │
│     - Returns structured scores                              │
│  4. Calculate Recommendation                                │
│  5. Save to Database                                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    HR REVIEW DASHBOARD                       │
│                                                              │
│  HR/Admin Views:                                             │
│  • Video with flag markers                                  │
│  • Transcript with timestamps                                │
│  • Scorecard (criteria scores + explanations)                │
│  • Flag list (all violations)                                │
│  • AI Recommendation                                         │
│                                                              │
│  HR/Admin Actions:                                           │
│  • Set final decision (PASS/REVIEW/FAIL)                    │
│  • Add review notes                                          │
│  • View/download clips                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Key Database Tables

### `ai_interview_sessions`
Stores session metadata and final scores:
- `id`: Session ID
- `application_id`: Links to candidate's application
- `job_id`: Links to job position
- `status`: CREATED → LIVE → FINALIZING → COMPLETED
- `total_score`: Final score (0.00-10.00)
- `recommendation`: AI recommendation (PASS/REVIEW/FAIL)
- `transcript_url`: URL to transcript file
- `report_json`: Full scoring report with citations

### `ai_proctor_flags`
Stores all proctoring violations:
- `session_id`: Links to interview session
- `flag_type`: Type of violation
- `severity`: LOW, MODERATE, HIGH
- `confidence`: Detection confidence (0.0-1.0)
- `t_start`, `t_end`: Time range of violation
- `clip_url`: URL to 6-10s video clip
- `flag_metadata`: Additional context

### `kb_docs`
Knowledge base for RAG scoring:
- Contains evaluation rubrics, criteria, job requirements
- Used for context-aware scoring

---

## 🔐 Security & Access Control

### Authentication
- All endpoints require JWT authentication
- Token stored in `localStorage` (frontend)

### Authorization Rules
```python
# HR/Admin only endpoints:
- POST /api/ai-interview/{session_id}/score
- POST /api/ai-interview/review/{session_id}/decision
- GET /api/ai-interview/kb/* (knowledge base management)

# Candidate or HR/Admin:
- GET /api/ai-interview/{session_id}/report
- GET /api/ai-interview/{session_id}/flags
- POST /api/ai-interview/{session_id}/events
```

### Data Privacy
- Candidates can only access their own interview data
- HR/Admin can access all interviews within their company
- Video/audio stored securely in MinIO/S3 with signed URLs

---

## 📈 Current Implementation Status

### ✅ Implemented
- Data collection (video, audio, flags)
- Database storage
- RAG-based scoring service
- HR review dashboard
- Flag generation and display

### 🚧 Partially Implemented
- Transcript storage (path exists, download logic TODO)
- Automatic scoring on interview end (manual trigger works)
- Candidate self-view (endpoint exists, UI not fully implemented)

### 📝 TODO
- Automatic scoring job queue (background worker)
- Transcript download and parsing
- Email notifications to candidates
- Integration with application status workflow
- Export reports (PDF generation)

---

## 🎯 Summary

**Where Data Goes:**
1. **PostgreSQL Database**: Session metadata, flags, scores
2. **MinIO/S3 Storage**: Video recordings, transcripts, clips
3. **Knowledge Base (pgvector)**: Evaluation rubrics for RAG

**How It's Evaluated:**
1. **RAG-Based Scoring**: Hybrid retrieval (BM25 + vector) + Ollama LLM
2. **Criteria-Based**: Scores multiple dimensions (technical, communication, etc.)
3. **Citation-Based**: Explanations reference knowledge base documents
4. **Recommendation**: Automatic PASS/REVIEW/FAIL based on scores + flags

**Who Sees It:**
1. **HR/Admin**: Full access to all interviews, can trigger scoring, set final decisions
2. **Candidates**: Can view their own interview (limited implementation)
3. **Interviewers**: No access (separate system for traditional interviews)

