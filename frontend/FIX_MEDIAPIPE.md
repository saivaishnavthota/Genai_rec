# Fix MediaPipe Module Not Found Error

## Problem
```
ERROR in ./src/lib/mediapipe.ts 5:0-74
Module not found: Error: Can't resolve '@mediapipe/tasks-vision'
```

## Solution

The package `@mediapipe/tasks-vision` is already installed (version 0.10.21), but the React dev server needs to be restarted to pick it up.

### Steps to Fix:

1. **Stop the React dev server** (Ctrl+C in the terminal where it's running)

2. **Clear the cache** (optional but recommended):
   ```powershell
   cd frontend
   Remove-Item -Recurse -Force node_modules/.cache
   ```

3. **Restart the dev server**:
   ```powershell
   cd frontend
   npm start
   ```

### Alternative: Reinstall Dependencies

If restarting doesn't work, try reinstalling:

```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
npm install
npm start
```

### Verify Installation

To verify the package is installed:
```powershell
cd frontend
npm list @mediapipe/tasks-vision
```

Should show: `@mediapipe/tasks-vision@0.10.21`

## Note

The package is already in `package.json` and installed in `node_modules`. This is a caching issue that requires restarting the dev server.

