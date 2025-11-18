# Health Check Script for HygiaAI Offline Deployment

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "Checking service health..." -ForegroundColor Yellow
Write-Host ""

# Check Qdrant
Write-Host -NoNewline "Qdrant: "
try {
    $response = Invoke-WebRequest -Uri "http://localhost:6333/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ Healthy" -ForegroundColor Green
} catch {
    Write-Host "✗ Unhealthy" -ForegroundColor Red
}

# Check Backend API
Write-Host -NoNewline "Backend API: "
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ Healthy" -ForegroundColor Green
} catch {
    Write-Host "✗ Unhealthy" -ForegroundColor Red
}

# Check Frontend
Write-Host -NoNewline "Frontend: "
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ Healthy" -ForegroundColor Green
} catch {
    Write-Host "⚠ Not responding (may be starting)" -ForegroundColor Yellow
}

# Check Docker containers
Write-Host ""
Write-Host "Docker container status:" -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "For detailed logs, run: docker-compose logs" -ForegroundColor Cyan

