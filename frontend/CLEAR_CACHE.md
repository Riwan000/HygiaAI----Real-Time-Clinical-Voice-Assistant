# Clear Vite Cache to Fix React Multiple Instance Error

## Problem
"Invalid hook call" errors occur when multiple copies of React are loaded. This happens when Vite's cache contains stale optimized dependencies.

## Solution

**IMPORTANT: Stop the dev server first!**

Then run these commands:

```powershell
# Navigate to frontend directory
cd frontend

# Remove Vite cache
Remove-Item -Recurse -Force node_modules\.vite -ErrorAction SilentlyContinue

# Remove dist directory (if it exists)
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue

# Restart dev server
npm run dev
```

Or use this one-liner:
```powershell
cd frontend; Remove-Item -Recurse -Force node_modules\.vite,dist -ErrorAction SilentlyContinue; npm run dev
```

## After Clearing Cache

1. **Hard refresh your browser**: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
2. **Check console**: You should no longer see "Invalid hook call" errors
3. **Verify React is working**: Components should render correctly

## If Issue Persists

If clearing cache doesn't work, try a full reinstall:

```powershell
cd frontend
Remove-Item -Recurse -Force node_modules,package-lock.json,.vite,dist -ErrorAction SilentlyContinue
npm install
npm run dev
```

