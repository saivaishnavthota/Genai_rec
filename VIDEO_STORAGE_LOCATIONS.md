# Video Storage Locations for AI Interview System

## 📍 Storage Locations

### **Primary Storage: MinIO/S3 Object Storage**

Videos are stored in MinIO/S3 (or AWS S3) with the following structure:

**⚠️ IMPORTANT:** Currently, MinIO storage is **NOT configured** (endpoint is empty). 
Videos will be stored in MinIO only if you:
1. Start MinIO server
2. Configure `MINIO_ENDPOINT` in `.env` file
3. Restart the backend

```
Bucket: interview-blobs
├── sessions/
│   ├── {session_id}/
│   │   ├── raw.mp4                    # Full video recording
│   │   ├── clips/
│   │   │   ├── flag_{flag_id}.mp4    # Video clips for each flag
│   │   └── artifacts/
│   │       └── transcript.json         # Transcript file
```

**Example paths:**
- Session 16 video: `sessions/16/raw.mp4`
- Session 16, Flag 1 clip: `sessions/16/clips/flag_1.mp4`
- Session 16 transcript: `sessions/16/artifacts/transcript.json`

### **Configuration**

Storage is configured in `backend/app/config.py`:
- **MinIO Endpoint**: `MINIO_ENDPOINT` (default: empty - disabled)
- **Bucket Name**: `S3_BUCKET` (default: `interview-blobs`)
- **Access Key**: `MINIO_ACCESS_KEY` (default: `minioadmin`)
- **Secret Key**: `MINIO_SECRET_KEY` (default: `minioadmin`)

## 🔍 How to Check if Videos Exist

### **Method 1: Using the Check Script**

Run the utility script to check storage:

```bash
# From project root directory
cd backend
python check_video_storage.py 16

# Or list all sessions
python check_video_storage.py
```

**Note:** This script will tell you if MinIO is configured and show file status.

### **Method 2: Using MinIO Console**

1. **Start Docker Desktop** (if not running)

2. **Start MinIO** (Windows PowerShell - single line):
   ```powershell
   docker run -d -p 9000:9000 -p 9001:9001 --name minio -e "MINIO_ROOT_USER=minioadmin" -e "MINIO_ROOT_PASSWORD=minioadmin" minio/minio server /data --console-address ":9001"
   ```

   **Or use the batch file:**
   ```cmd
   start-minio.bat
   ```

2. Open MinIO Console: http://localhost:9001
   - Login: `minioadmin` / `minioadmin`
   - Navigate to bucket: `interview-blobs`
   - Browse to: `sessions/16/raw.mp4`

### **Method 3: Using Python Script**

```python
from app.ai_interview.services.storage_service import StorageService

storage = StorageService()

# Check if video exists
video_path = "sessions/16/raw.mp4"
try:
    obj = storage.client.stat_object("interview-blobs", video_path)
    print(f"Video exists! Size: {obj.size / (1024*1024):.2f} MB")
except Exception as e:
    print(f"Video not found: {e}")
```

### **Method 4: Using MinIO Client (mc)**

```bash
# Install MinIO client
# Windows: Download from https://min.io/download

# Configure alias
mc alias set myminio http://localhost:9000 minioadmin minioadmin

# List files
mc ls myminio/interview-blobs/sessions/16/

# Check specific file
mc stat myminio/interview-blobs/sessions/16/raw.mp4
```

### **Method 5: Check Database**

Videos may be stored in the database or referenced:

```sql
-- Check session video URL
SELECT id, video_url, transcript_url, status 
FROM ai_interview_sessions 
WHERE id = 16;

-- Check flag clips
SELECT id, flag_type, clip_url, t_start, t_end 
FROM ai_proctor_flags 
WHERE session_id = 16;
```

## ⚠️ Important Notes

1. **If MinIO is NOT configured** (`MINIO_ENDPOINT` is empty):
   - Videos will NOT be stored in MinIO
   - The system will try to use API endpoints instead
   - Videos must be uploaded manually or via another mechanism

2. **Video Upload**:
   - Currently, videos are expected to be uploaded to storage when interview ends
   - If using WebRTC, you need to implement video upload logic
   - The system assumes videos exist at `sessions/{session_id}/raw.mp4`

3. **Local Storage (Alternative)**:
   - If MinIO is not available, you can store videos locally
   - Update `video_url` in database to point to local file path
   - The API endpoint will serve from local filesystem

## 🛠️ Troubleshooting

### Video Not Found Error

1. **Check if MinIO is running:**
   ```bash
   docker ps | grep minio
   ```

2. **Check configuration:**
   ```bash
   # Check .env file
   cat backend/.env | grep MINIO
   ```

3. **Verify file exists in storage:**
   ```bash
   python backend/check_video_storage.py 16
   ```

4. **Check database:**
   ```sql
   SELECT video_url FROM ai_interview_sessions WHERE id = 16;
   ```

### Setting Up MinIO

1. **Start MinIO:**
   ```bash
   docker run -d -p 9000:9000 -p 9001:9001 \
     --name minio \
     -e "MINIO_ROOT_USER=minioadmin" \
     -e "MINIO_ROOT_PASSWORD=minioadmin" \
     -v minio_data:/data \
     minio/minio server /data --console-address ":9001"
   ```

2. **Configure in .env:**
   ```bash
   MINIO_ENDPOINT=localhost:9000
   MINIO_ACCESS_KEY=minioadmin
   MINIO_SECRET_KEY=minioadmin
   S3_BUCKET=interview-blobs
   S3_USE_SSL=false
   ```

3. **Restart backend** to apply changes

## 📊 Summary

- **Storage Type**: MinIO/S3 Object Storage
- **Bucket**: `interview-blobs`
- **Path Format**: `sessions/{session_id}/raw.mp4`
- **Clips Path**: `sessions/{session_id}/clips/flag_{flag_id}.mp4`
- **Default Endpoint**: `localhost:9000` (if configured)
- **Check Script**: `python backend/check_video_storage.py [session_id]`

