# Fix: AI Interview Storage Issues

## Problem Summary
The AI interview system was not storing:
- **Videos**: No endpoint to upload video recordings to MinIO
- **Transcripts**: Transcripts were generated but not saved to MinIO (TODO comment)
- **Flags**: Flags were being saved to database correctly ✅
- **Scorecards**: Couldn't be generated without transcripts

## Fixes Applied

### 1. ✅ Added Video Upload Endpoint
**File**: `backend/app/ai_interview/routers/proctor.py`

Added new endpoint: `POST /api/ai-interview/{session_id}/upload-video`

- Accepts video file uploads (MP4)
- Saves to MinIO at `sessions/{session_id}/raw.mp4`
- Updates session `video_url` in database
- Includes proper authentication and authorization

**Usage**:
```bash
curl -X POST \
  http://localhost:8000/api/ai-interview/{session_id}/upload-video \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "video_file=@recording.mp4"
```

### 2. ✅ Fixed Transcript Storage
**File**: `backend/app/ai_interview/routers/asr.py`

- Removed TODO comment
- Actually uploads transcript JSON to MinIO at `sessions/{session_id}/artifacts/transcript.json`
- Updates session `transcript_url` in database

### 3. ✅ Verified Flags Storage
**File**: `backend/app/ai_interview/routers/proctor.py`

Flags are already being saved correctly:
- Client events are processed by `ProctorService.process_client_events()`
- Flags are created and saved to `ai_proctor_flags` table
- No changes needed ✅

### 4. ✅ Added Logging for Transcription
**File**: `backend/app/ai_interview/routers/proctor.py`

Added logging when interview ends to indicate transcription can be triggered.

## Configuration Required

### 1. Enable MinIO Storage

**Check your `.env` file or `backend/app/config.py`**:

```bash
# MinIO Configuration
MINIO_ENDPOINT=localhost:9000  # ⚠️ Currently set to empty string!
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
S3_BUCKET=interview-blobs
S3_USE_SSL=false
```

**Current Issue**: `minio_endpoint` is set to `""` (empty string) in `config.py`, which disables storage.

**Fix**: Set `MINIO_ENDPOINT=localhost:9000` in your `.env` file or update `config.py`.

### 2. Ensure MinIO is Running

```bash
# Check if MinIO is running
docker ps | grep minio

# If not running, start it:
docker run -d -p 9000:9000 -p 9001:9001 \
  --name minio \
  -e 'MINIO_ROOT_USER=minioadmin' \
  -e 'MINIO_ROOT_PASSWORD=minioadmin' \
  minio/minio server /data --console-address ':9001'

# Or use the provided script:
start-minio.bat
```

### 3. Frontend Integration Needed

The frontend needs to:
1. **Record video** during the interview (using MediaRecorder API)
2. **Upload video** when interview ends via `POST /api/ai-interview/{session_id}/upload-video`
3. **Trigger transcription** via `POST /api/ai-interview/{session_id}/transcribe` (optional, can be automatic)

## Next Steps

### For Frontend Developers:

1. **Add Video Recording**:
   ```typescript
   // In AIInterviewRoomPage.tsx or similar
   const mediaRecorderRef = useRef<MediaRecorder | null>(null);
   
   useEffect(() => {
     if (mediaDevices.stream && stage === 'live') {
       const recorder = new MediaRecorder(mediaDevices.stream, {
         mimeType: 'video/webm;codecs=vp9'
       });
       mediaRecorderRef.current = recorder;
       recorder.start();
     }
   }, [mediaDevices.stream, stage]);
   ```

2. **Upload Video on Interview End**:
   ```typescript
   const handleInterviewEnd = async () => {
     if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
       mediaRecorderRef.current.stop();
       mediaRecorderRef.current.ondataavailable = async (event) => {
         if (event.data.size > 0) {
           const formData = new FormData();
           formData.append('video_file', event.data, 'recording.webm');
           
           await fetch(`/api/ai-interview/${sessionId}/upload-video`, {
             method: 'POST',
             headers: {
               'Authorization': `Bearer ${token}`
             },
             body: formData
           });
         }
       };
     }
   };
   ```

### For Backend Verification:

1. **Check MinIO Connection**:
   ```bash
   # Check backend logs for:
   # ✅ MinIO client initialized successfully: localhost:9000
   # OR
   # ⚠️  MinIO server is not running at localhost:9000
   ```

2. **Test Video Upload**:
   ```bash
   curl -X POST \
     http://localhost:8000/api/ai-interview/6/upload-video \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "video_file=@test.mp4"
   ```

3. **Check MinIO Console**:
   - Open http://localhost:9001
   - Login: minioadmin / minioadmin
   - Check `interview-blobs` bucket
   - Should see: `sessions/{session_id}/raw.mp4`

## Summary

✅ **Fixed**:
- Video upload endpoint added
- Transcript storage fixed
- Flags already working correctly

⚠️ **Action Required**:
- Set `MINIO_ENDPOINT=localhost:9000` in `.env`
- Ensure MinIO is running
- Frontend needs to record and upload videos

📝 **Files Modified**:
- `backend/app/ai_interview/routers/proctor.py` - Added video upload endpoint
- `backend/app/ai_interview/routers/asr.py` - Fixed transcript storage

