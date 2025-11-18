# Test Script for Offline Deployment Kit
# This script validates the deployment configuration without starting services

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "HygiaAI Offline Deployment Kit - Test" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0
$WarningCount = 0

# Test 1: Check Docker
Write-Host "Test 1: Checking Docker..." -ForegroundColor Yellow
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCmd) {
    $dockerVersion = docker --version 2>&1
    Write-Host "  ✓ Docker found: $dockerVersion" -ForegroundColor Green
} else {
    Write-Host "  ✗ Docker not found" -ForegroundColor Red
    $ErrorCount++
}

# Test 2: Check Docker Compose
Write-Host "Test 2: Checking Docker Compose..." -ForegroundColor Yellow
$composeCmd = Get-Command docker-compose -ErrorAction SilentlyContinue
if ($composeCmd) {
    $composeVersion = docker-compose --version 2>&1
    Write-Host "  ✓ Docker Compose found: $composeVersion" -ForegroundColor Green
} else {
    Write-Host "  ✗ Docker Compose not found" -ForegroundColor Red
    $ErrorCount++
}

# Test 3: Validate docker-compose.yml syntax
Write-Host "Test 3: Validating docker-compose.yml..." -ForegroundColor Yellow
$composeFile = "docker-compose.yml"
if (Test-Path $composeFile) {
    $result = docker-compose -f $composeFile config --quiet 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ docker-compose.yml is valid" -ForegroundColor Green
    } else {
        Write-Host "  ✗ docker-compose.yml has errors" -ForegroundColor Red
        Write-Host "    $result" -ForegroundColor Red
        $ErrorCount++
    }
} else {
    Write-Host "  ✗ docker-compose.yml not found" -ForegroundColor Red
    $ErrorCount++
}

# Test 4: Check required files
Write-Host "Test 4: Checking required files..." -ForegroundColor Yellow
$requiredFiles = @(
    "Dockerfile.backend",
    "Dockerfile.frontend",
    "nginx.conf",
    "install.ps1",
    "start.ps1",
    "stop.ps1",
    "health-check.ps1",
    "env.offline.example"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file (missing)" -ForegroundColor Red
        $ErrorCount++
    }
}

# Test 5: Check port availability
Write-Host "Test 5: Checking port availability..." -ForegroundColor Yellow
$ports = @(3000, 8000, 6333)
foreach ($port in $ports) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        Write-Host "  ⚠ Port $port is in use" -ForegroundColor Yellow
        $WarningCount++
    } else {
        Write-Host "  ✓ Port $port is available" -ForegroundColor Green
    }
}

# Test 6: Validate Dockerfiles exist and are readable
Write-Host "Test 6: Validating Dockerfiles..." -ForegroundColor Yellow
$dockerfiles = @(
    "Dockerfile.backend",
    "Dockerfile.frontend"
)

foreach ($dockerfile in $dockerfiles) {
    if (Test-Path $dockerfile) {
        $content = Get-Content $dockerfile -Raw
        if ($content -match "FROM") {
            Write-Host "  ✓ $dockerfile is valid" -ForegroundColor Green
        } else {
            Write-Host "  ✗ $dockerfile appears invalid" -ForegroundColor Red
            $ErrorCount++
        }
    } else {
        Write-Host "  ✗ $dockerfile not found" -ForegroundColor Red
        $ErrorCount++
    }
}

# Test 7: Check environment file template
Write-Host "Test 7: Checking environment configuration..." -ForegroundColor Yellow
$envFile = "env.offline.example"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile
    $requiredVars = @("QDRANT_HOST", "QDRANT_PORT", "OFFLINE_MODE")
    $foundVars = 0
    foreach ($var in $requiredVars) {
        if ($envContent -match $var) {
            $foundVars++
        }
    }
    if ($foundVars -eq $requiredVars.Count) {
        Write-Host "  ✓ Environment template contains required variables" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Some required variables missing in template" -ForegroundColor Yellow
        $WarningCount++
    }
} else {
    Write-Host "  ✗ Environment template not found" -ForegroundColor Red
    $ErrorCount++
}

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
if ($ErrorCount -eq 0) {
    Write-Host "Errors: $ErrorCount" -ForegroundColor Green
} else {
    Write-Host "Errors: $ErrorCount" -ForegroundColor Red
}
if ($WarningCount -eq 0) {
    Write-Host "Warnings: $WarningCount" -ForegroundColor Green
} else {
    Write-Host "Warnings: $WarningCount" -ForegroundColor Yellow
}

if ($ErrorCount -eq 0) {
    Write-Host ""
    Write-Host "✓ All critical tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Review warnings (if any)" -ForegroundColor White
    Write-Host "2. Run: .\install.ps1" -ForegroundColor White
    Write-Host "3. Configure: Edit .env.offline file" -ForegroundColor White
    Write-Host "4. Start: .\start.ps1" -ForegroundColor White
    exit 0
} else {
    Write-Host ""
    Write-Host "✗ Some tests failed. Please fix errors before proceeding." -ForegroundColor Red
    exit 1
}
