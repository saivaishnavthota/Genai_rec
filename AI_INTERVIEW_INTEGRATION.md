# AI Interview Proctor Integration Guide

## Where AI Interview Has Been Added

The AI Interview Proctor has been integrated into the **Application Details** page at **two key points** in the hiring workflow:

### Integration Points

#### 1. **Shortlisted Status** (`shortlisted`)
- **Location**: Application Details page
- **Action**: "Start AI Interview" button appears alongside "Schedule Interview"
- **When**: When an application status is `shortlisted`
- **Flow**: 
  1. HR reviews application
  2. Clicks "Shortlist"
  3. Can now choose:
     - **Traditional Interview**: "Schedule Interview" (Google Meet with human interviewers)
     - **AI Interview**: "Start AI Interview" (AI-led with automated proctoring)

#### 2. **Selected Status** (`selected`)
- **Location**: Application Details page
- **Action**: "Start AI Interview" button appears alongside "Fetch Availability"
- **When**: When an application status is `selected`
- **Flow**:
  1. Application is selected after resume update/improvement
  2. HR can choose:
     - **Traditional Interview**: "Fetch Availability" → Candidate selects slot → Schedule with interviewers
     - **AI Interview**: "Start AI Interview" → Immediate AI interview session

## Complete Workflow

### Traditional Interview Flow
```
Application → Shortlisted → Schedule Interview → Fetch Availability → 
Slot Selected → Interview Confirmed → Interview Completed → Review Received → Hired/Rejected
```

### AI Interview Flow (NEW)
```
Application → Shortlisted → Start AI Interview → 
  ↓
Candidate Interview Room (/ai-interview/:sessionId)
  ↓
AI Proctoring (head pose, face detection, audio monitoring)
  ↓
Automated Scoring (RAG-based with Ollama)
  ↓
HR Review Dashboard (/review/ai-interview/:sessionId)
  ↓
HR Decision → Hired/Rejected
```

## How to Use

### For HR/Admin:

1. **Navigate to Application Details**
   - Go to Applications page
   - Click on any application

2. **Start AI Interview**
   - When application is `shortlisted` or `selected`
   - Click **"Start AI Interview"** button
   - System creates a session and redirects to interview room

3. **Share Interview Link**
   - After starting, you'll get a session ID
   - Share this link with candidate: `/ai-interview/:sessionId`
   - Or candidate can access via their application status page

4. **Review AI Interview**
   - After candidate completes interview
   - Navigate to: `/review/ai-interview/:sessionId`
   - View:
     - Video recording with flag markers
     - Automated scorecard
     - Transcript with questions
     - Proctoring flags (head-turn, face-absent, etc.)
   - Make final decision: Hire/Reject

### For Candidates:

1. **Receive Interview Link**
   - Via email or application status page
   - Link format: `http://localhost:3000/ai-interview/:sessionId`

2. **Complete Interview**
   - Pre-check: Test camera/microphone
   - Consent: Accept monitoring terms
   - Calibration: Align head pose
   - Live Interview: Answer questions
   - End Interview: Submit responses

3. **Wait for Results**
   - HR reviews AI-scored interview
   - Receives decision notification

## API Endpoints

### Start AI Interview
```http
POST /api/ai-interview/start
Authorization: Bearer <token>
Content-Type: application/json

{
  "application_id": 123,
  "job_id": 45
}

Response:
{
  "session_id": 789,
  "webrtc_token": "token...",
  "policy_version": "1.0",
  "rubric_version": "1.0"
}
```

### Get Interview Report
```http
GET /api/ai-interview/:sessionId/report
Authorization: Bearer <token>

Response:
{
  "session_id": 789,
  "total_score": 85.5,
  "recommendation": "strong_hire",
  "scores": { ... },
  "flags": [ ... ],
  "transcript": "..."
}
```

## Status Integration

The AI Interview integrates with existing application statuses:

- **`shortlisted`**: Can start AI interview OR schedule traditional interview
- **`selected`**: Can start AI interview OR fetch availability for traditional interview
- **After AI Interview**: HR makes decision → `hired` or `rejected`

## Notes

- AI Interview is **optional** - HR can still use traditional interviews
- AI Interview provides **automated scoring** and **proctoring**
- Traditional interviews still use **human interviewers** via Google Meet
- Both paths lead to the same final decision point

