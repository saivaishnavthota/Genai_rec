# Why MediaPipe Error Keeps Occurring

## Root Cause

The error happens because:
1. ✅ `@mediapipe/tasks-vision` is **listed** in `package.json`
2. ❌ But it's **NOT actually installed** in `node_modules`

## Why This Happens

This occurs when:
- Dependencies were installed **before** the package was added to `package.json`
- Installation was interrupted or failed silently
- `node_modules` was deleted but not reinstalled
- Package was added manually to `package.json` but `npm install` wasn't run

## The Fix

You **MUST** run a clean install to actually install the package:

```cmd
cd frontend
clean-install.bat
```

Or manually:
```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json
npm install
```

## Why It Keeps Happening

The error persists because:
- **Just restarting the dev server won't fix it** - the package still isn't installed
- **The package.json has it** - but that's just a list, not the actual installation
- **node_modules doesn't have it** - so the import fails

## Verification

After running clean install, verify:
```powershell
cd frontend
npm list @mediapipe/tasks-vision
```

Should show: `@mediapipe/tasks-vision@0.10.21`

Also check:
```powershell
Test-Path node_modules/@mediapipe/tasks-vision
```

Should return: `True`

## Prevention

After adding any package to `package.json`:
1. Always run `npm install` to actually install it
2. Verify installation with `npm list <package-name>`
3. Check `node_modules` folder exists

## Quick Fix Right Now

Run this command to fix it immediately:

```cmd
cd frontend
clean-install.bat
```

This will:
- Remove node_modules
- Remove package-lock.json
- Clear npm cache
- Reinstall everything from package.json
- Install MediaPipe properly

