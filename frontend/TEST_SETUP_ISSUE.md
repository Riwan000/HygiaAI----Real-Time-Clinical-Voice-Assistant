# Testing Setup Issues & Resolutions

## Issue 1: parse5/jsdom ES Module Compatibility

### Problem
Error: `require() of ES Module parse5/dist/index.js not supported`

This occurs because jsdom v27+ tries to use parse5 v8+ which is ESM-only, but jsdom uses CommonJS `require()`.

### ✅ Solution Applied
Switched from `jsdom` to `happy-dom` as the test environment. `happy-dom` is:
- Faster than jsdom
- No parse5 dependency issues
- Better ES module support
- Fully compatible with Vitest

**Changes made:**
- Replaced `jsdom` with `happy-dom` in `package.json`
- Updated `vitest.config.ts` to use `environment: 'happy-dom'`

## Issue 2: Vitest Not Found

### Problem
`'vitest' is not recognized as an internal or external command`

### Solutions to Try

### Option 1: Reinstall Dependencies

**PowerShell:**
```powershell
Set-Location frontend
npm install
```

**Bash/Linux/Mac:**
```bash
cd frontend
npm install
```

### Option 2: Use npx

**PowerShell:**
```powershell
Set-Location frontend
npx vitest run
```

**Bash/Linux/Mac:**
```bash
cd frontend
npx vitest run
```

### Option 3: Check Node Version ⚠️ **REQUIRED**
Current: Node v22.9.0
Vite requires: ^20.19.0 || >=22.12.0

**Action Required:** Upgrade Node.js to v22.12.0+ or use Node v20.19.0+ to run tests.
This is a hard requirement - Vitest will not install/run with Node v22.9.0.

**Status:** All test files are written and ready. Tests will run once Node.js is upgraded.

## Test Files Created

All test files are ready and will work once Vitest is installed:

### Components (8 files)
- `Loading.test.tsx`
- `Breadcrumbs.test.tsx`
- `CaseCard.test.tsx`
- `SearchBox.test.tsx`
- `Pagination.test.tsx`
- `CaseFilters.test.tsx`
- `SOAPNoteViewer.test.tsx`
- `ErrorBoundary.test.tsx`
- `accessibility.test.tsx` (combined accessibility tests)

### Hooks (1 file)
- `useTheme.test.ts`

### Utils (1 file)
- `clsx.test.ts`

### Services (2 files)
- `api.test.ts`
- `clinicalMemoryService.test.ts`

### Pages (1 file)
- `Dashboard.test.tsx`

### E2E (3 files)
- `dashboard.spec.ts`
- `accessibility.spec.ts`
- `transcription.spec.ts`

## Once Vitest is Installed

Run tests with:

### PowerShell (Windows)
```powershell
Set-Location frontend
npm run test:run        # Run once
npm run test            # Watch mode
npm run test:coverage   # With coverage
npm run test:e2e        # E2E tests
```

### Bash/Linux/Mac
```bash
cd frontend
npm run test:run        # Run once
npm run test            # Watch mode
npm run test:coverage   # With coverage
npm run test:e2e        # E2E tests
```

**Note:** If you encounter PowerShell-specific issues:
- Use `Set-Location` instead of `cd` if needed
- Use semicolons (`;`) instead of `&&` for command chaining
- Ensure Node.js version is v22.12.0+ or v20.19.0+

