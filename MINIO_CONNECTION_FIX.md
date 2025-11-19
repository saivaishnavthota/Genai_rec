# MinIO Connection Fix

## Problem
MinIO connection was failing with retry warnings:
```
WARNING:urllib3.connectionpool:Retrying ... Failed to establish a new connection: [WinError 10061] No connection could be made because the target machine actively refused it
```

## Root Cause
- MinIO endpoint was configured but the server was not running
- The storage service was attempting connections that would retry multiple times
- No graceful handling when MinIO is unavailable

## Fixes Applied

### 1. **Suppressed urllib3 Warnings**
- Added `urllib3.disable_warnings()` to suppress connection retry warnings
- Prevents log spam when MinIO is not available

### 2. **Fast Connection Test**
- Added socket-based connection test (2-second timeout)
- Fails fast instead of hanging on retries
- Detects connection issues before attempting MinIO operations

### 3. **Better Error Handling**
- Checks if storage client is available before operations
- Gracefully falls back to API endpoints when storage is unavailable
- Clearer error messages with instructions

### 4. **Improved Logging**
- Changed warning messages to debug level for normal fallback scenarios
- Only shows warnings for actual configuration issues
- Provides clear instructions on how to start MinIO

## How to Start MinIO

### Option 1: Using the Batch File (Windows)
```cmd
start-minio.bat
```

### Option 2: Using Docker Command
```powershell
docker run -d -p 9000:9000 -p 9001:9001 --name minio -e "MINIO_ROOT_USER=minioadmin" -e "MINIO_ROOT_PASSWORD=minioadmin" minio/minio server /data --console-address ":9001"
```

### Option 3: Check if MinIO is Already Running
```powershell
docker ps | findstr minio
```

If MinIO container exists but is stopped:
```powershell
docker start minio
```

## Configuration

Make sure `backend/.env` has:
```env
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
S3_BUCKET=interview-blobs
S3_USE_SSL=false
```

## Verification

After starting MinIO:
1. Check MinIO Console: http://localhost:9001
   - Login: `minioadmin` / `minioadmin`
2. Check backend logs - should see:
   ```
   ✅ MinIO client initialized successfully: localhost:9000
   ```
3. Run the check script:
   ```bash
   python backend/check_video_storage.py
   ```

## Behavior When MinIO is Not Available

The system will:
- ✅ Continue running without errors
- ✅ Use API endpoints for video/clip serving
- ✅ Log clear warnings (not errors)
- ✅ Provide instructions on how to start MinIO

## Notes

- The app works without MinIO (uses API endpoints for media)
- MinIO is optional but recommended for production
- Videos/clips can be served through the API even without MinIO
- Storage is only needed for presigned URLs and direct file access

