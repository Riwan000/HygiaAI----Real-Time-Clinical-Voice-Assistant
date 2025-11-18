# Start HygiaAI Offline Deployment

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "Starting HygiaAI services..." -ForegroundColor Yellow

# Check if .env.offline exists
if (-not (Test-Path ".env.offline")) {
    Write-Host "Error: .env.offline not found. Please copy .env.offline.example to .env.offline and configure it." -ForegroundColor Red
    exit 1
}

# Start services with docker-compose
docker-compose up -d

Write-Host "Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service health
.\health-check.ps1

Write-Host ""
Write-Host "Services started successfully!" -ForegroundColor Green
Write-Host "Access the application at:"
Write-Host "  Frontend: http://localhost:3000"
Write-Host "  Backend API: http://localhost:8000"
Write-Host "  API Docs: http://localhost:8000/docs"
Write-Host "  Qdrant Dashboard: http://localhost:6333/dashboard"
Write-Host ""

