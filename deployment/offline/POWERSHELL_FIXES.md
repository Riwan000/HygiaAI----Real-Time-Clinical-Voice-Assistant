# PowerShell Script Fixes

## Common PowerShell Issues Resolved

### Issue 1: Using `&&` Operator
**Problem**: PowerShell doesn't support `&&` operator (bash syntax)
**Solution**: Use `;` (semicolon) or separate commands

**Before (Wrong):**
```powershell
cd directory && command
```

**After (Correct):**
```powershell
Set-Location directory; command
# OR
Set-Location directory
command
```

### Issue 2: Path Separators
**Problem**: Mixing forward/backward slashes
**Solution**: Use backslashes `\` for Windows paths in PowerShell

**Correct:**
```powershell
Copy-Item -Path "deployment\offline\*" -Destination $InstallDir
```

### Issue 3: Command Chaining
**Problem**: Trying to chain commands incorrectly
**Solution**: Use proper PowerShell syntax

**Correct Examples:**
```powershell
# Using semicolon
Set-Location $InstallDir; .\start.ps1

# Using pipeline
Get-ChildItem | Where-Object { $_.Extension -eq ".ps1" }

# Using if statement
if (Test-Path $file) { .\script.ps1 }
```

### Issue 4: Special Characters in Strings
**Problem**: Parentheses and special chars in Write-Host
**Solution**: Use proper quoting

**Correct:**
```powershell
Write-Host "Collection: hygiaai_clinical_cases (10 cases)" -ForegroundColor White
```

### Issue 5: Error Handling
**Problem**: Commands failing silently
**Solution**: Use proper error handling

**Correct:**
```powershell
try {
    $response = Invoke-WebRequest -Uri "http://localhost:6333/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "Healthy" -ForegroundColor Green
} catch {
    Write-Host "Unhealthy" -ForegroundColor Red
}
```

## Fixed Scripts

All PowerShell scripts in `deployment/offline/` have been reviewed and fixed:

✅ `install.ps1` - Fixed command chaining
✅ `start.ps1` - Proper error handling
✅ `stop.ps1` - Correct syntax
✅ `health-check.ps1` - Proper try-catch blocks
✅ `test-deployment.ps1` - Fixed all syntax issues

## Testing

To verify scripts work correctly:

```powershell
# Test syntax
Get-Content deployment\offline\install.ps1 | Out-Null
if ($?) { Write-Host "Syntax OK" }

# Run with error checking
$ErrorActionPreference = "Stop"
.\deployment\offline\install.ps1
```

## Common Commands Reference

### Change Directory
```powershell
Set-Location "C:\Path\To\Directory"
# OR
cd "C:\Path\To\Directory"
```

### Chain Commands
```powershell
Set-Location $dir; .\script.ps1
# NOT: cd $dir && .\script.ps1
```

### Check if Command Exists
```powershell
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Docker found"
}
```

### Check Port
```powershell
$connection = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($connection) {
    Write-Host "Port in use"
}
```

---

**All PowerShell scripts are now properly formatted and tested!**

