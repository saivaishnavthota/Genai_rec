# AI Interview Storage Diagnosis

## Current Status

### ✅ What's Working:
1. **Flags are being saved to database** - Logs show `"Saved {len(flags)} flags to database for session {session_id}"`
2. **Client events are being received** - Frontend is sending head pose and face detection events
3. **MinIO is configured** - `MINIO_ENDPOINT=minio:9000` is set in Docker container
4. **Backend endpoints exist** - Video upload and transcript endpoints are available

### ❌ What's NOT Working:

#### 1. **Video Recording is NOT Happening**
- **Frontend**: No `MediaRecorder` implementation found
- **Frontend**: `handleEndInterview()` only calls `endInterview()` API, doesn't upload video
- **Result**: No video files are being created or uploaded

#### 2. **Video Upload is NOT Being Called**
- **Frontend**: No code to record video during interview
- **Frontend**: No code to upload video when interview ends
- **Backend**: `POST /api/ai-interview/{session_id}/upload-video` endpoint exists but is never called

#### 3. **Transcription is NOT Being Triggered**
- **Backend**: `POST /api/ai-interview/{session_id}/transcribe` endpoint exists
- **Frontend**: No code to trigger transcription
- **Backend**: No automatic transcription when interview ends

#### 4. **StorageService May Not Be Initializing**
- **Issue**: No logs showing "MinIO client initialized successfully"
- **Possible Cause**: StorageService is initialized lazily (only when first used)
- **Impact**: Even if video was uploaded, storage might not be available

## What the Logs Show

### During Interview:
```
INFO: Processing {len(request.events)} client events for session {session_id}
INFO: Generated {len(flags)} flags from events
INFO: Saved {len(flags)} flags to database for session {session_id}
```

### What's Missing:
- ❌ No "MinIO client initialized" messages
- ❌ No video upload requests
- ❌ No transcription requests
- ❌ No storage operations

## Root Cause Analysis

### Problem 1: Frontend Doesn't Record Video
**Location**: `frontend/src/pages/AIInterviewRoomPage.tsx`

**Current Code** (line 230-253):
```typescript
const handleEndInterview = async () => {
  // ... stops tracking ...
  await aiInterviewAPI.endInterview(parseInt(sessionId));
  // ❌ NO VIDEO RECORDING OR UPLOAD
};
```

**Missing**:
- MediaRecorder to record video stream
- Code to upload video blob when interview ends

### Problem 2: StorageService May Not Be Connected
**Location**: `backend/app/ai_interview/services/storage_service.py`

**Issue**: StorageService initializes in `__init__`, but:
- If MinIO connection fails, it silently sets `self.client = None`
- No error is raised, so the app continues without storage
- First storage operation will fail with "Storage client not initialized"

### Problem 3: No Automatic Transcription
**Location**: `backend/app/ai_interview/routers/proctor.py` (end_interview endpoint)

**Current Code**:
```python
# Try to transcribe audio if video is available (non-blocking)
# Note: This requires the video to be uploaded first via /upload-video endpoint
# For now, we'll just log that transcription should be triggered manually
```

**Issue**: Transcription is not automatic - requires manual trigger or video upload

## Solutions

### Solution 1: Add Video Recording to Frontend

**File**: `frontend/src/pages/AIInterviewRoomPage.tsx`

Add MediaRecorder:
```typescript
const mediaRecorderRef = useRef<MediaRecorder | null>(null);
const recordedChunksRef = useRef<Blob[]>([]);

// Start recording when interview starts
useEffect(() => {
  if (stage === 'live' && mediaDevices.stream) {
    const recorder = new MediaRecorder(mediaDevices.stream, {
      mimeType: 'video/webm;codecs=vp9,opus'
    });
    
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        recordedChunksRef.current.push(event.data);
      }
    };
    
    recorder.start(1000); // Collect data every second
    mediaRecorderRef.current = recorder;
  }
}, [stage, mediaDevices.stream]);

// Upload video when interview ends
const handleEndInterview = async () => {
  // ... existing code ...
  
  // Stop recording
  if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
    mediaRecorderRef.current.stop();
    
    // Wait for final data
    await new Promise((resolve) => {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.onstop = async () => {
          const blob = new Blob(recordedChunksRef.current, { type: 'video/webm' });
          
          // Upload video
          const formData = new FormData();
          formData.append('video_file', blob, `session-${sessionId}.webm`);
          
          try {
            await apiClient.post(`/api/ai-interview/${sessionId}/upload-video`, formData, {
              headers: { 'Content-Type': 'multipart/form-data' }
            });
            console.log('Video uploaded successfully');
          } catch (error) {
            console.error('Failed to upload video:', error);
          }
          
          recordedChunksRef.current = [];
          resolve();
        };
      }
    });
  }
  
  await aiInterviewAPI.endInterview(parseInt(sessionId));
};
```

### Solution 2: Verify StorageService Initialization

**Check**: Add logging to see if StorageService initializes:

```python
# In storage_service.py __init__
logger.info(f"StorageService.__init__ called")
logger.info(f"MinIO endpoint: {self.endpoint}")
if self.client:
    logger.info("✅ StorageService initialized with MinIO client")
else:
    logger.warning("⚠️ StorageService initialized WITHOUT MinIO client")
```

### Solution 3: Add Automatic Transcription Trigger

**File**: `backend/app/ai_interview/routers/proctor.py`

Modify `end_interview` to trigger transcription:
```python
# After video is uploaded, trigger transcription
if session.video_url and _storage_service.is_available():
    try:
        # Download video from storage
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp_path = tmp.name
        
        _storage_service.download_file(session.video_url, tmp_path)
        
        # Extract audio and transcribe
        transcript = await _asr_service.transcribe_file(tmp_path, with_timestamps=True)
        
        # Save transcript
        transcript_path = _storage_service.get_transcript_path(session_id)
        import json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_json:
            json.dump(transcript, tmp_json, indent=2)
            _storage_service.upload_file(tmp_json.name, transcript_path, content_type="application/json")
        
        session.transcript_url = transcript_path
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to transcribe automatically: {e}")
```

## Immediate Action Items

1. **Check StorageService initialization**:
   ```bash
   docker logs genai-backend | grep -i "storage\|minio"
   ```

2. **Test MinIO connection from backend**:
   ```bash
   docker exec genai-backend python -c "from app.ai_interview.services.storage_service import StorageService; s = StorageService(); print(f'Available: {s.is_available()}')"
   ```

3. **Add video recording to frontend** (see Solution 1 above)

4. **Test video upload**:
   ```bash
   curl -X POST http://localhost:8000/api/ai-interview/6/upload-video \
     -H "Authorization: Bearer TOKEN" \
     -F "video_file=@test.mp4"
   ```

## Summary

**The main issue**: The frontend is NOT recording or uploading video during interviews. All the backend infrastructure is in place, but the frontend needs to:
1. Record video using MediaRecorder
2. Upload video when interview ends
3. Optionally trigger transcription

**Flags are working** ✅ - They're being saved to the database correctly.

**Storage is configured** ✅ - MinIO endpoint is set correctly.

**Missing piece**: Frontend video recording and upload implementation.

