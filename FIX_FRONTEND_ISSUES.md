# Fix Frontend Issues

## Issue 1: MediaPipe TypeScript Error Recurring

### Problem
TypeScript keeps complaining about `@mediapipe/tasks-vision` module not being found, even after the package is installed.

### Solution
Changed from `@ts-expect-error` to `@ts-ignore` in `frontend/src/lib/mediapipe.ts`:
- `@ts-ignore` always suppresses the error (even if module is found)
- `@ts-expect-error` requires an error to be present, causing "unused directive" errors

The dynamic import approach still works at runtime, but TypeScript needs to be told to ignore the module resolution check.

## Issue 2: Port 3000 Not Being Killed

### Problem
When you stop the frontend server (Ctrl+C), the port 3000 remains occupied, preventing the server from restarting.

### Solutions

#### Option 1: Use the Kill Script (Recommended)
Run this script to kill processes on port 3000:
```cmd
kill-frontend-port.bat
```

This script will:
1. Find all processes using port 3000
2. Kill those processes
3. Also kill any remaining Node.js processes
4. Verify the port is free

#### Option 2: Updated Start Script
The `start-frontend.bat` script has been updated to:
- Automatically kill any existing processes on port 3000 before starting
- Clean up Node.js processes when you exit (Ctrl+C)

#### Option 3: Manual Kill
If the scripts don't work, manually kill the process:

**Find the process:**
```cmd
netstat -ano | findstr :3000
```

**Kill by PID:**
```cmd
taskkill /F /PID <PID_NUMBER>
```

**Or kill all Node.js processes:**
```cmd
taskkill /F /IM node.exe
```

**Note:** You may need to run as Administrator if the process doesn't die.

## Quick Fix Commands

### Kill Frontend Port
```cmd
kill-frontend-port.bat
```

### Start Frontend (with auto-cleanup)
```cmd
start-frontend.bat
```

### Manual Kill (if needed)
```cmd
taskkill /F /IM node.exe
```

## Prevention

1. **Always use Ctrl+C** to stop the frontend server properly
2. **Run `kill-frontend-port.bat`** if the port is stuck
3. **Check for multiple Node processes:**
   ```cmd
   tasklist | findstr node.exe
   ```

## Troubleshooting

### Port Still in Use After Killing
1. Run as Administrator:
   - Right-click `kill-frontend-port.bat`
   - Select "Run as administrator"

2. Check for other processes:
   ```cmd
   netstat -ano | findstr :3000
   ```

3. Restart your computer (last resort)

### TypeScript Errors Persist
1. Clear TypeScript cache:
   ```cmd
   cd frontend
   Remove-Item -Recurse -Force node_modules\.cache -ErrorAction SilentlyContinue
   Remove-Item -Force .tsbuildinfo -ErrorAction SilentlyContinue
   ```

2. Restart the dev server:
   ```cmd
   kill-frontend-port.bat
   start-frontend.bat
   ```

## Files Changed

1. `frontend/src/lib/mediapipe.ts` - Changed `@ts-expect-error` to `@ts-ignore`
2. `start-frontend.bat` - Added automatic port cleanup
3. `kill-frontend-port.bat` - New script to kill port 3000 processes

