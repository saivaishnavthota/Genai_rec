# AI Interview Proctoring Flags System - Complete Explanation

## Issues You Reported

### 1. ❌ **Timestamp Mismatch (Flags show 1+ minute, video ends at 0:53)**
### 2. ❌ **Score 8.2/10 showing FAIL result**
### 3. ❌ **Phone detected at 0:00 seconds (false positive)**
### 4. ⚠️ **Timeout 30000ms error on first Trigger Scoring**

---

## Issue #1: Timestamp Mismatch Explanation

### The Problem
- Video duration: **0:53 seconds (53 seconds)**
- Flags showing timestamps: **1:13, 1:14, 1:15, 1:16, 1:17, 1:19, 1:20, 1:21** (70-81 seconds)

### Root Cause: **Incorrect Timestamp Calculation**

**Code Location:** [backend/app/ai_interview/routers/proctor.py:747-751](backend/app/ai_interview/routers/proctor.py#L747-L751)

```python
# Calculate timestamp based on sampled frames
# Each sampled frame represents 0.5 seconds (since we sample 2 per second)
timestamp = sampled_frame_count * 0.5
sampled_frame_count += 1
frame_count += 1
```

### The Issue
The algorithm samples frames at **2 frames per second** (every Nth frame based on FPS), but then assigns timestamps as:
- Frame 0 → 0.0 seconds
- Frame 1 → 0.5 seconds
- Frame 2 → 1.0 seconds
- ...
- Frame 160 → 80 seconds

**BUT** the actual video is only **53 seconds long**!

### Why This Happens
1. Video has actual FPS (e.g., 30 fps)
2. Frame interval calculated: `frame_interval = max(1, int(fps / 2))` = 15 frames
3. Code samples every 15th frame
4. But timestamp calculation assumes **exactly 2 samples per second**, which isn't accurate if:
   - FPS is not exactly divisible by 2
   - Video has variable frame rate
   - Frame drops or encoding issues

### The Actual Calculation
```python
# Current (WRONG):
timestamp = sampled_frame_count * 0.5

# Should be:
actual_frame_number = frame_count
timestamp = actual_frame_number / fps
```

**Example with your video:**
- Video: 30 FPS, 53 seconds → 1,590 total frames
- Sampling every 15th frame → 106 sampled frames
- Current calc: 106 * 0.5 = **53 seconds** ✅ (accidentally correct!)
- But if FPS detection is wrong (e.g., 25 FPS detected instead of 30):
  - 106 * 0.5 = 53 seconds (calc)
  - Actual: 106 * 15 / 25 = **63.6 seconds** (reality mismatch)

### Code Reference
**File:** `backend/app/ai_interview/routers/proctor.py`
**Lines:** 720-751

```python
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0  # ⚠️ If FPS detection fails, defaults to 30
duration = total_frames / fps if fps > 0 else 0

frame_interval = max(1, int(fps / 2))  # Sample 2 frames per second
logger.info(f"📊 Sampling every {frame_interval} frames (2 frames/second)")

# PROBLEM: This assumes perfect 0.5s intervals
timestamp = sampled_frame_count * 0.5  # ❌ WRONG
```

---

## Issue #2: Score 8.2/10 Showing FAIL - Explained

### Your Result
- **Score:** 8.2/10 (above passing threshold of 7.0)
- **Result:** FAIL ❌
- **Expected:** PASS ✅ or REVIEW 🔍

### The Recommendation Algorithm

**Code Location:** [backend/app/ai_interview/services/interview_service.py:329-364](backend/app/ai_interview/services/interview_service.py#L329-L364)

```python
def calculate_recommendation(self, db: Session, session_id: int) -> Recommendation:
    """
    Calculate recommendation based on score and flags

    Policy:
    - Auto-PASS: final_score ≥ 7.0 AND no HIGH flags AND ≤2 MODERATE flags
    - Auto-FAIL: ≥2 HIGH flags OR explicit policy breach
    - Else: REVIEW
    """
    session = db.query(AISession).filter(AISession.id == session_id).first()
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Get flags
    flags = db.query(AISessionFlag).filter(
        AISessionFlag.session_id == session_id
    ).all()

    high_flags = [f for f in flags if f.severity == FlagSeverity.HIGH]
    moderate_flags = [f for f in flags if f.severity == FlagSeverity.MODERATE]

    # Check for auto-fail
    if len(high_flags) >= 2:
        return Recommendation.FAIL  # ⚠️ THIS IS WHY YOU GOT FAIL

    # Check for auto-pass
    if session.total_score and session.total_score >= Decimal("7.0"):
        if len(high_flags) == 0 and len(moderate_flags) <= 2:
            return Recommendation.PASS

    return Recommendation.REVIEW
```

### Your Case Analysis

Looking at your screenshot:
- **HIGH severity flags:** 8 flags (Multiple Faces detected 8 times)
  - 1:13.664, 1:14.432, 1:15.152, 1:16.287, 1:17.024, 1:19.647, 1:20.415, 1:21.152, 1:21.888
- **MODERATE severity flags:** 2 flags (Phone Detected 2 times)
  - 0:00.000, 0:00.000

### Why FAIL?
```python
if len(high_flags) >= 2:  # 8 HIGH flags >= 2
    return Recommendation.FAIL  # ✅ Auto-FAIL triggered
```

**Policy Logic:**
- ≥2 HIGH severity flags = **Automatic FAIL** (regardless of score)
- Your video had **8 HIGH flags** (multiple faces detected)
- Even with 8.2/10 score, the system failed you due to proctoring violations

### Is This Correct Behavior?

**YES** - This is the intended design:
- High-severity proctoring violations (cheating indicators) override good performance
- Multiple people in frame = potential cheating
- System prioritizes integrity over score

**HOWEVER** - In your case, these are **FALSE POSITIVES**:
- Timestamps are wrong (beyond video duration)
- Face detection might be oversensitive

---

## Issue #3: Phone Detected at 0:00 Seconds (False Positive)

### Your Screenshot Shows
```
0:00.000  Phone Detected  MODERATE
0:00.000  Phone Detected  MODERATE
```

### How Phone Detection Works

**Code Location:** [backend/app/ai_interview/services/proctor_service.py:242-349](backend/app/ai_interview/services/proctor_service.py#L242-L349)

#### Step 1: Image Processing
```python
def detect_phone_in_frame(self, frame: np.ndarray, timestamp: float):
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Adaptive thresholding for edge detection
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 2
    )

    # Canny edge detection
    edges = cv2.Canny(blurred, 30, 100)

    # Combine both methods
    combined = cv2.bitwise_or(thresh, edges)
```

#### Step 2: Find Rectangular Objects
```python
# Find contours
contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

for contour in contours:
    # Get bounding rectangle
    x, y, rect_w, rect_h = cv2.boundingRect(contour)

    # Size filter (3-30% of frame)
    min_size = min(w, h) * 0.03
    max_size = min(w, h) * 0.30

    # Aspect ratio check (1.2:1 to 4:1 - phone-like)
    aspect_ratio = max(rect_w, rect_h) / min(rect_w, rect_h)
    if aspect_ratio < 1.2 or aspect_ratio > 4.5:
        continue  # Not phone-shaped
```

#### Step 3: Position and Shape Validation
```python
# Check if in lower 70% of frame (where hands hold phones)
is_lower_portion = y > h * 0.3

# Or in center area
is_center_area = (x > w * 0.2 and x < w * 0.8) and (y > h * 0.2 and y < h * 0.8)

# How rectangular is it? (phones are rectangular)
extent = area / rect_area
if extent > 0.5:  # At least 50% rectangular
    # Calculate confidence
    confidence = min(0.85, (size_score * 0.3 + aspect_score * 0.3 + extent_score * 0.4))
```

### Why False Positives at 0:00?

**Possible Causes:**

1. **Your Hand in Frame**
   - Hand holding something rectangular (remote, pen, notebook)
   - Aspect ratio matches phone (1.5:1 to 3:1)
   - In lower portion of frame
   - Confidence ≥ 0.50 threshold

2. **Background Objects**
   - Picture frames on wall
   - Book spines
   - Monitor bezels
   - Any rectangular object

3. **Lighting/Shadows**
   - Strong edge contrasts
   - Shadows creating false rectangles
   - Light reflections

4. **Edge Detection Sensitivity**
   ```python
   edges = cv2.Canny(blurred, 30, 100)  # Low thresholds = more sensitive
   ```
   - Current thresholds (30, 100) are **very low**
   - Detects even weak edges
   - More false positives

### The Flag Tracker Logic

**Code Location:** [backend/app/ai_interview/utils/flag_tracker.py:73-149](backend/app/ai_interview/utils/flag_tracker.py#L73-L149)

```python
def update(self, t: float, conf: float, metadata: Optional[Dict] = None):
    meets_threshold = conf >= self.min_conf  # Phone: min_conf = 0.60

    if meets_threshold:
        if self.active_start is None:
            # Start tracking
            self.active_start = t  # Started at t=0.0
            self.max_conf = conf
        else:
            # Update max confidence
            self.max_conf = max(self.max_conf, conf)

        duration = t - self.active_start

        # Check if duration threshold met
        if duration >= self.min_duration:  # Phone: 1.0 second
            # Emit flag with 2s pre/post roll
            window = FlagWindow(
                t_start=max(0, self.active_start - 2.0),  # 0.0 - 2.0 = -2.0 → 0.0
                t_end=t + 2.0,
                confidence=self.max_conf,
                severity=severity,
                metadata=self.metadata.copy()
            )
            return window
```

### Why Two Flags at 0:00?

**Scenario:**
1. Frame at 0.0s: Phone detected (conf=0.65)
2. Frame at 0.5s: Phone detected (conf=0.70)
3. Duration: 0.5s < 1.0s threshold → **No flag yet**
4. Frame at 1.0s: Phone detected (conf=0.75)
5. Duration: 1.0s ≥ 1.0s → **Flag emitted** with t_start=0.0
6. Tracker resets, cooldown starts
7. Frame at 2.0s: Phone detected again (conf=0.68)
8. Cooldown expired (1.0s passed)
9. Duration: 1.0s ≥ 1.0s → **Second flag emitted** with t_start=0.0

**Result:** Two MODERATE flags both showing 0:00.000

---

## Issue #4: Timeout 30000ms Error

### The Error
```
Timeout 30000ms error when clicking "Trigger Scoring"
```

### Why This Happens

**Code Location:** [backend/app/services/llm_service.py:28-42](backend/app/services/llm_service.py#L28-L42)

```python
async def _chat_ollama(self, messages: list, temperature: Optional[float] = None,
                       max_tokens: Optional[int] = None, timeout: Optional[int] = None):
    # Use custom timeout if provided, otherwise use default
    request_timeout = timeout if timeout is not None else self.timeout  # Default: 120s

    # Convert to httpx.Timeout
    if isinstance(request_timeout, int):
        timeout_obj = httpx.Timeout(request_timeout, connect=10.0)
    else:
        timeout_obj = request_timeout

    async with httpx.AsyncClient(timeout=timeout_obj) as client:
        r = await client.post(f"{self.ollama_base}/api/chat", json=payload)
```

### Scoring Process

**Code Location:** [backend/app/ai_interview/routers/scoring.py](backend/app/ai_interview/routers/scoring.py)

The scoring process involves:
1. **Transcribe video** (if not already done) - Uses Whisper ASR
2. **Load transcript** - From MinIO storage
3. **Analyze with LLM** - Uses Ollama to score responses
4. **Calculate recommendation** - Based on scores and flags

### Timeout Causes

1. **First Time Slower:**
   - Ollama model needs to load into memory
   - Whisper model initialization
   - First-time processing takes 60-120 seconds
   - Default API timeout: 30 seconds ❌

2. **Large Video Files:**
   - Your video: 53 seconds → ~10-20 MB
   - Transcription can take 2-5x real-time
   - 53 seconds video = 2-5 minutes processing

3. **Model Performance:**
   - Ollama model size (3B parameters)
   - CPU vs GPU processing
   - Available RAM/VRAM

### Why Second Attempt Succeeded

- Models already loaded in memory
- Transcript already generated and cached
- Only needs to run scoring LLM
- Faster: 10-30 seconds

### Fix Needed
Increase API timeout or make async with status polling.

---

## Complete Flow: How Flags Work

### 1. Video Recording (Frontend)
```typescript
// frontend/src/pages/AIInterviewRoomPage.tsx
const recorder = new MediaRecorder(mediaDevices.stream);

recorder.ondataavailable = (event) => {
  if (event.data && event.data.size > 0) {
    recordedChunksRef.current.push(event.data);
  }
};

// On interview end
await aiInterviewAPI.uploadVideo(sessionId, videoBlob);
```

### 2. Video Upload & Processing (Backend)
```python
# backend/app/ai_interview/routers/proctor.py:638-639
# Trigger video analysis for flags (phone detection, multi-face detection)
background_tasks.add_task(_analyze_video_for_flags_async, session_id, video_path)
```

### 3. Frame-by-Frame Analysis
```python
async def _analyze_video_for_flags_async(session_id: int, video_path: str):
    # Download video from MinIO
    _storage_service.download_file(video_path, tmp_path)

    # Open video
    cap = cv2.VideoCapture(tmp_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    # Sample 2 frames per second
    frame_interval = max(1, int(fps / 2))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Every Nth frame
        if frame_count % frame_interval != 0:
            frame_count += 1
            continue

        timestamp = sampled_frame_count * 0.5  # ⚠️ ISSUE HERE

        # Detect phone
        phone_detection = _proctor_service.detect_phone_in_frame(frame, timestamp)
        if phone_detection and phone_detection['confidence'] >= 0.50:
            window = phone_tracker.update(timestamp, conf, metadata)
            if window:
                flag = create_flag(...)
                flags_created.append(flag)

        # Detect multiple faces
        face_detection = _proctor_service.detect_faces_in_frame(frame, timestamp)
        if face_detection['face_count'] > 1:
            window = multi_face_tracker.update(timestamp, 1.0, metadata)
            if window:
                flag = create_flag(...)
                flags_created.append(flag)
```

### 4. Flag Tracker Debouncing
```python
# backend/app/ai_interview/utils/flag_tracker.py
class FlagTracker:
    def update(self, t: float, conf: float, metadata: Dict):
        if conf >= self.min_conf:
            if self.active_start is None:
                self.active_start = t  # Start tracking

            duration = t - self.active_start

            if duration >= self.min_duration:  # e.g., 1.0s for phone
                if t - self.last_emit_time >= self.cooldown:  # e.g., 1.0s cooldown
                    # Emit flag
                    return FlagWindow(
                        t_start=max(0, self.active_start - 2.0),  # Add 2s pre-roll
                        t_end=t + 2.0,  # Add 2s post-roll
                        confidence=self.max_conf,
                        severity=severity
                    )
```

### 5. Save Flags to Database
```python
# Save flags to database
if flags_created:
    for flag in flags_created:
        db.add(flag)
    db.commit()
    logger.info(f"✅ Created {len(flags_created)} flags")
```

### 6. Scoring & Recommendation
```python
# backend/app/ai_interview/services/interview_service.py
def calculate_recommendation(self, db: Session, session_id: int):
    high_flags = [f for f in flags if f.severity == FlagSeverity.HIGH]
    moderate_flags = [f for f in flags if f.severity == FlagSeverity.MODERATE]

    # Auto-FAIL if ≥2 HIGH flags
    if len(high_flags) >= 2:
        return Recommendation.FAIL

    # Auto-PASS if score ≥7.0 AND no HIGH AND ≤2 MODERATE
    if session.total_score >= 7.0:
        if len(high_flags) == 0 and len(moderate_flags) <= 2:
            return Recommendation.PASS

    return Recommendation.REVIEW
```

### 7. Display in UI
- Frontend polls `/api/ai-interview/{session_id}/flags`
- Displays flags in timeline
- Shows severity colors (LOW=yellow, MODERATE=orange, HIGH=red)
- Recommendation shown based on algorithm

---

## Summary of Issues

| Issue | Root Cause | Impact | Code Location |
|-------|-----------|--------|---------------|
| **Timestamps beyond video** | Incorrect timestamp calculation using `sampled_frame_count * 0.5` instead of `frame_number / fps` | Flags show times that don't exist in video | `proctor.py:749` |
| **8.2 score = FAIL** | 8 HIGH flags (≥2) triggers auto-FAIL regardless of score | Correct behavior but based on false positives | `interview_service.py:355-356` |
| **False phone detection at 0:00** | Overly sensitive edge detection + low confidence threshold (0.50) | Detects hands, objects, shadows as phones | `proctor_service.py:267-278` |
| **Timeout 30000ms** | First scoring takes 60-120s (model loading + transcription) but API timeout is 30s | First click fails, second succeeds (cached) | `llm_service.py:37-42` |

---

## Recommendations for Fixes

### 1. Fix Timestamp Calculation
```python
# Current (WRONG):
timestamp = sampled_frame_count * 0.5

# Fixed (CORRECT):
actual_frame_position = frame_count
timestamp = actual_frame_position / fps
```

### 2. Adjust Phone Detection Sensitivity
```python
# Increase confidence threshold
if conf >= 0.70:  # Changed from 0.50 to 0.70

# Or increase Canny edge thresholds
edges = cv2.Canny(blurred, 50, 150)  # Changed from (30, 100)
```

### 3. Increase Scoring Timeout
```python
# In API client or backend
timeout_obj = httpx.Timeout(180.0, connect=10.0)  # 3 minutes instead of 30s
```

### 4. Add Progress Indicator
Show "Scoring in progress..." with status updates instead of hard timeout.

---

## Code Files Involved

| File | Purpose | Key Functions |
|------|---------|---------------|
| `backend/app/ai_interview/routers/proctor.py:672-862` | Video analysis background task | `_analyze_video_for_flags_async()` |
| `backend/app/ai_interview/services/proctor_service.py:242-349` | Phone detection algorithm | `detect_phone_in_frame()` |
| `backend/app/ai_interview/services/proctor_service.py:50-100` | Face detection algorithm | `detect_faces_in_frame()` |
| `backend/app/ai_interview/utils/flag_tracker.py:39-149` | Flag debouncing logic | `FlagTracker.update()` |
| `backend/app/ai_interview/services/interview_service.py:329-364` | Recommendation calculation | `calculate_recommendation()` |
| `backend/app/services/llm_service.py:28-42` | LLM API calls with timeout | `_chat_ollama()` |

---

## Testing the System

### Check Video FPS Detection
```bash
docker exec -it genai-backend python -c "
import cv2
cap = cv2.VideoCapture('/app/uploads/sessions/2/raw.mp4')
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = total_frames / fps
print(f'FPS: {fps}, Frames: {total_frames}, Duration: {duration:.2f}s')
cap.release()
"
```

### Check Flags in Database
```bash
docker exec -it genai-postgres psql -U postgres -d genai_hiring -c "
SELECT id, flag_type, severity, t_start, t_end, confidence
FROM ai_session_flags
WHERE session_id = 2
ORDER BY t_start;
"
```

### View Backend Logs
```bash
docker logs genai-backend | grep -E "(📱|👥|🚨|VIDEO ANALYSIS)"
```
