# Migration from MediaPipe to face-api.js

## Why the Change?

MediaPipe has been causing recurring issues:
- Module resolution problems in Docker
- Webpack cache issues
- Complex setup requirements
- Frequent build failures

**face-api.js** is a better alternative because:
- ✅ Simpler installation (just `npm install`)
- ✅ Works reliably in Docker/containers
- ✅ No webpack cache issues
- ✅ Models load from CDN (no local files)
- ✅ Similar face detection capabilities
- ✅ Better maintained and documented

## What Changed?

1. **New Package**: `@vladmandic/face-api` replaces `@mediapipe/tasks-vision`
2. **New Module**: `src/lib/faceDetection.ts` replaces `src/lib/mediapipe.ts`
3. **Same API**: The interface is compatible, so existing code works with minimal changes

## Migration Steps

### 1. Install the New Package

**Local Development:**
```bash
cd frontend
npm install @vladmandic/face-api --save
```

**Docker:**
```bash
# Rebuild the frontend container
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### 2. Remove MediaPipe (Optional)

You can keep MediaPipe in package.json for now, or remove it:
```bash
npm uninstall @mediapipe/tasks-vision
```

### 3. Verify It Works

1. Start the application
2. Navigate to an AI interview
3. Check browser console - you should see:
   - "Loading face-api.js models..."
   - "face-api.js models loaded successfully"
   - Face detection working without errors

## Features

The new implementation provides:
- ✅ Face detection (detect faces in video)
- ✅ Face landmarks (68 points)
- ✅ Head pose estimation (yaw, pitch, roll)
- ✅ Face count
- ✅ Confidence scores

## Troubleshooting

### Models Not Loading

If models fail to load from CDN, they'll be cached automatically. Check browser console for errors.

### Performance

face-api.js is slightly slower than MediaPipe but more reliable. For most use cases, the difference is negligible.

### Fallback

If face-api.js fails, the system will gracefully degrade - face detection will return null but won't crash the app.

## Rollback (if needed)

If you need to go back to MediaPipe:
1. Revert changes to `src/hooks/useHeadPose.ts`
2. Change import back to `../lib/mediapipe`
3. Rebuild Docker container

But we recommend staying with face-api.js for better reliability.

