# Clean Install - Remove and Reinstall All Dependencies

## Quick Fix

Run the batch file:
```cmd
cd frontend
clean-install.bat
```

Or use the fix script (same thing):
```cmd
cd frontend
fix-mediapipe.bat
```

## Manual Steps

If you prefer to do it manually:

```powershell
cd frontend

# 1. Stop dev server (if running)
# Press Ctrl+C in the terminal where npm start is running

# 2. Remove node_modules
Remove-Item -Recurse -Force node_modules

# 3. Remove package-lock.json
Remove-Item -Force package-lock.json

# 4. Clear npm cache (optional but recommended)
npm cache clean --force

# 5. Reinstall all dependencies
npm install

# 6. Verify MediaPipe is installed
npm list @mediapipe/tasks-vision

# 7. Start dev server
npm start
```

## What This Does

1. **Stops any running dev server** - Prevents file lock issues
2. **Removes node_modules** - Clears all installed packages
3. **Removes package-lock.json** - Ensures fresh dependency resolution
4. **Clears npm cache** - Removes any cached corrupted packages
5. **Reinstalls everything** - Fresh install of all dependencies from package.json
6. **Verifies MediaPipe** - Confirms the package is properly installed

## Why This Works

- Removes any corrupted or incomplete installations
- Ensures all dependencies are installed from scratch
- Resolves any version conflicts or missing packages
- Fixes cache-related issues

## Expected Output

After running, you should see:
```
+ @mediapipe/tasks-vision@0.10.21
```

And the dev server should start without the MediaPipe error.

## Troubleshooting

If you still get errors after clean install:

1. **Check Node.js version:**
   ```powershell
   node --version
   ```
   Should be 14.x or higher

2. **Try with different npm version:**
   ```powershell
   npm install -g npm@latest
   ```

3. **Check internet connection** - npm needs to download packages

4. **Try with yarn instead:**
   ```powershell
   npm install -g yarn
   yarn install
   ```

