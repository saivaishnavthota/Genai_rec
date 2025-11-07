# Fix MediaPipe Module Not Found Error

## Problem
```
Module not found: Error: Can't resolve '@mediapipe/tasks-vision' in '/app/src/lib'
```

Even after restarting, the error persists because the package is not actually installed in `node_modules`.

## Solution

### Option 1: Run the Fix Script (Recommended)
```cmd
cd frontend
fix-mediapipe.bat
```

This script will:
1. Stop any running dev server
2. Clear React cache
3. Remove node_modules and package-lock.json
4. Reinstall all dependencies
5. Verify MediaPipe installation

### Option 2: Manual Fix

1. **Stop the dev server** (Ctrl+C)

2. **Clear cache and reinstall:**
   ```powershell
   cd frontend
   
   # Clear cache
   Remove-Item -Recurse -Force node_modules\.cache -ErrorAction SilentlyContinue
   
   # Remove node_modules
   Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
   
   # Remove package-lock.json
   Remove-Item -Force package-lock.json -ErrorAction SilentlyContinue
   
   # Reinstall all dependencies
   npm install
   ```

3. **Verify installation:**
   ```powershell
   npm list @mediapipe/tasks-vision
   ```
   
   Should show: `@mediapipe/tasks-vision@0.10.21`

4. **Start dev server:**
   ```powershell
   npm start
   ```

### Option 3: Quick Fix (If others don't work)

```powershell
cd frontend
npm install @mediapipe/tasks-vision --force
npm start
```

## Why This Happens

- The package is in `package.json` but not in `node_modules`
- This can happen if:
  - Installation was interrupted
  - Dependencies were installed before the package was added
  - Cache corruption
  - npm/yarn lock file issues

## Verification

After fixing, you should see:
- ✅ No compilation errors
- ✅ MediaPipe imports work
- ✅ Dev server starts successfully

## If Still Not Working

1. Check Node.js version:
   ```powershell
   node --version
   ```
   Should be 14+ or 16+

2. Clear npm cache:
   ```powershell
   npm cache clean --force
   ```

3. Try installing with specific version:
   ```powershell
   npm install @mediapipe/tasks-vision@0.10.21 --save-exact
   ```

