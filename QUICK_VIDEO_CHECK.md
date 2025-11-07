# Quick Guide: Check Video Storage

## 🔍 Where Videos Are Stored

### **Storage Paths:**
- **Full Video**: `sessions/{session_id}/raw.mp4` in MinIO bucket `interview-blobs`
- **Flag Clips**: `sessions/{session_id}/clips/flag_{flag_id}.mp4`
- **Transcripts**: `sessions/{session_id}/artifacts/transcript.json`

### **Example for Session 16:**
- Video: `sessions/16/raw.mp4`
- Clip for Flag 1: `sessions/16/clips/flag_1.mp4`

## ✅ Quick Check Methods

### **1. Check Database (Fastest)**
```sql
-- Check if video URL is set
SELECT id, video_url, transcript_url, status 
FROM ai_interview_sessions 
WHERE id = 16;

-- Check flags and their clips
SELECT id, flag_type, clip_url, t_start, t_end 
FROM ai_proctor_flags 
WHERE session_id = 16;
```

### **2. Run Check Script**
```bash
# From project root
cd backend
python check_video_storage.py 16
```

### **3. Check via API**
Visit: `http://localhost:8000/api/ai-interview/16/video?token=YOUR_TOKEN`
- Returns 404 if video doesn't exist
- Returns video stream if it exists

### **4. MinIO Console (If MinIO is Running)**
1. Open: http://localhost:9001
2. Login: `minioadmin` / `minioadmin`
3. Navigate to bucket: `interview-blobs`
4. Browse: `sessions/16/`

## ⚙️ Current Status

**MinIO Configuration:**
- Endpoint: `""` (empty - NOT configured)
- Bucket: `interview-blobs`
- **Status**: Storage is disabled

**To Enable Storage:**
1. Start Docker Desktop
2. Run: `start-minio.bat` (or the docker command)
3. Add to `backend/.env`:
   ```
   MINIO_ENDPOINT=localhost:9000
   MINIO_ACCESS_KEY=minioadmin
   MINIO_SECRET_KEY=minioadmin
   S3_BUCKET=interview-blobs
   ```
4. Restart backend server

## 🚨 Why Videos Might Be Missing

1. **MinIO not configured** - Videos won't be stored
2. **Video upload not implemented** - WebRTC recording needs to upload to storage
3. **Storage connection failed** - Check MinIO is running
4. **Wrong path** - Video uploaded to different location

## 📝 Next Steps

1. **Check database** - See if `video_url` is set
2. **Run check script** - See storage status
3. **Implement video upload** - If using WebRTC, add upload logic when recording ends
4. **Enable MinIO** - If you want to use object storage

