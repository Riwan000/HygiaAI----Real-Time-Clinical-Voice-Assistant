# Test PowerShell Script Syntax
# This script validates all PowerShell scripts in the deployment directory

Write-Host "Testing PowerShell script syntax..." -ForegroundColor Cyan
Write-Host ""

$scripts = @(
    "install.ps1",
    "start.ps1",
    "stop.ps1",
    "health-check.ps1",
    "test-deployment.ps1"
)

$allPassed = $true

foreach ($script in $scripts) {
    if (Test-Path $script) {
        Write-Host -NoNewline "Testing $script... "
        try {
            $content = Get-Content $script -Raw
            $errors = $null
            $null = [System.Management.Automation.PSParser]::Tokenize($content, [ref]$errors)
            if ($errors.Count -eq 0) {
                Write-Host "OK" -ForegroundColor Green
            } else {
                Write-Host "Errors Found" -ForegroundColor Red
                $allPassed = $false
            }
        } catch {
            Write-Host "Error: $_" -ForegroundColor Red
            $allPassed = $false
        }
    } else {
        Write-Host "$script - Not found" -ForegroundColor Yellow
    }
}

Write-Host ""
if ($allPassed) {
    Write-Host "All scripts passed syntax validation!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some scripts have syntax errors" -ForegroundColor Red
    exit 1
}
