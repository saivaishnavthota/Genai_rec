# Fix MediaPipe Webpack Cache Issue

## Problem

The error occurs intermittently:
```
ERROR in ./src/lib/mediapipe.ts 5:0-74
Module not found: Error: Can't resolve '@mediapipe/tasks-vision' in '/app/src/lib'
```

**Symptoms:**
- Works fine on first load
- Fails after navigating back from an interview
- Persists even after restarting the dev server
- Webpack loses track of the module after hot module reloading

## Root Cause

This is a **webpack module resolution cache issue**. When using static imports, webpack tries to resolve modules at build time. After hot module reloading (HMR) or certain navigation patterns, webpack's module cache can become corrupted, causing it to lose track of the `@mediapipe/tasks-vision` module.

## Solution Implemented

### 1. Dynamic Import (Primary Fix)

The code has been updated to use **dynamic imports** instead of static imports. This prevents webpack from trying to resolve the module at build time, avoiding cache issues.

**Before:**
```typescript
import { FaceLandmarker, FilesetResolver } from '@mediapipe/tasks-vision';
```

**After:**
```typescript
// Module is loaded dynamically when needed
const module = await import('@mediapipe/tasks-vision');
const { FaceLandmarker, FilesetResolver } = module;
```

### 2. Retry Logic

Added automatic retry logic if the module fails to load:
- First attempt: Load the module
- If it fails: Wait 1 second and retry once
- If retry fails: Throw a clear error message

### 3. Module Cache Management

- Module is cached after first successful load
- Cache is reset on errors to allow recovery
- Added `resetMediaPipeCache()` function for manual reset if needed

## How to Fix When It Happens

### Quick Fix (Recommended)

Run the webpack cache clearing script:

```cmd
cd frontend
fix-webpack-cache.bat
npm start
```

This script will:
1. Stop the dev server
2. Clear webpack cache
3. Clear TypeScript cache
4. Verify MediaPipe package installation
5. Clear npm cache

### Manual Fix

If the script doesn't work, do a full clean install:

```cmd
cd frontend
fix-mediapipe.bat
npm start
```

Or manually:

```powershell
cd frontend

# Stop dev server (Ctrl+C if running)

# Clear all caches
Remove-Item -Recurse -Force node_modules\.cache -ErrorAction SilentlyContinue
Remove-Item -Force .tsbuildinfo -ErrorAction SilentlyContinue

# Reinstall MediaPipe
npm install @mediapipe/tasks-vision --force

# Start dev server
npm start
```

## Prevention

The dynamic import solution should **prevent this issue from occurring** in the future. However, if you still encounter it:

1. **Clear webpack cache** - Run `fix-webpack-cache.bat`
2. **Check package installation** - Verify with `npm list @mediapipe/tasks-vision`
3. **Full clean install** - Run `fix-mediapipe.bat` if needed

## Technical Details

### Why Dynamic Imports Work

- **Static imports**: Webpack analyzes and bundles at build time, creating a dependency graph that can get corrupted
- **Dynamic imports**: Webpack creates a separate chunk that's loaded at runtime, avoiding build-time resolution issues

### Module Loading Flow

1. `initializeMediaPipe()` is called
2. `loadMediaPipeModule()` dynamically imports `@mediapipe/tasks-vision`
3. Module is cached for subsequent uses
4. If error occurs, cache is cleared and can be retried

## Verification

After applying the fix, you should see:
- ✅ No compilation errors
- ✅ MediaPipe loads successfully on first use
- ✅ No errors when navigating back from interviews
- ✅ Console logs show "Loading MediaPipe module dynamically..."

## If Still Not Working

1. **Verify Node.js version**: Should be 14+ or 16+
   ```powershell
   node --version
   ```

2. **Check package installation**:
   ```powershell
   npm list @mediapipe/tasks-vision
   ```
   Should show: `@mediapipe/tasks-vision@0.10.21`

3. **Full clean install**:
   ```cmd
   cd frontend
   clean-install.bat
   ```

4. **Check for conflicting packages**:
   ```powershell
   npm list --depth=0
   ```

## Related Files

- `frontend/src/lib/mediapipe.ts` - Main MediaPipe wrapper (updated with dynamic imports)
- `frontend/fix-webpack-cache.bat` - Script to clear webpack cache
- `frontend/fix-mediapipe.bat` - Script for full clean install
- `frontend/fix-mediapipe-cache.bat` - Alternative cache clearing script

