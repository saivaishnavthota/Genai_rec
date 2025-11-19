# Fix Backend Not Running in Docker

## Problem
Backend container fails to start with error:
```
ModuleNotFoundError: No module named 'minio'
```

## Root Cause
The Docker image was built before `minio` was added to `requirements.txt`, or the image needs to be rebuilt.

## Solutions

### Solution 1: Quick Fix (Temporary)
Install the missing package in the running container:

```cmd
fix-backend-deps.bat
```

Or manually:
```cmd
docker-compose exec backend pip install minio>=7.2.0
docker-compose restart backend
```

**Note:** This is temporary - if you rebuild the container, you'll need to do this again.

### Solution 2: Rebuild Backend Image (Recommended)
Rebuild the backend image to include all dependencies:

```cmd
docker-compose build --no-cache backend
docker-compose up -d backend
```

This will:
- Rebuild the backend image from scratch
- Install all packages from `requirements.txt` including `minio`
- Take 5-10 minutes on first build

### Solution 3: Rebuild All Services
If other services also need updates:

```cmd
docker-compose build --no-cache
docker-compose up -d
```

## Verification

After fixing, check backend logs:
```cmd
docker-compose logs backend
```

You should see:
- ✅ No `ModuleNotFoundError`
- ✅ Server starting successfully
- ✅ "Application startup complete"

Check container status:
```cmd
docker-compose ps backend
```

Should show "healthy" status.

## Prevention

Always rebuild images after adding dependencies to `requirements.txt`:
```cmd
docker-compose build backend
docker-compose up -d backend
```

## Additional Notes

### Why This Happens
- Docker images are built with dependencies from `requirements.txt`
- If `minio` was added after the image was built, it won't be available
- Volume mounts don't affect installed packages, but the image needs rebuilding

### Volume Mounts
The backend code is mounted as a volume (`./backend:/app`), which means:
- ✅ Code changes are reflected immediately
- ✅ But installed packages come from the Docker image
- ✅ So you need to rebuild when adding new dependencies

## Quick Commands

```cmd
# Quick fix (temporary)
fix-backend-deps.bat

# Proper fix (rebuild)
docker-compose build backend
docker-compose up -d backend

# Check status
docker-compose ps
docker-compose logs backend
```

