# PowerShell script to set up Qdrant for HygiaAI

Write-Host "Setting up Qdrant for HygiaAI..." -ForegroundColor Cyan

# Check if Docker is installed
try {
    docker --version | Out-Null
} catch {
    Write-Host "Error: Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if Qdrant is already running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:6333/health" -UseBasicParsing -TimeoutSec 2
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Qdrant is already running on localhost:6333" -ForegroundColor Green
        exit 0
    }
} catch {
    # Qdrant is not running, continue
}

# Check if container already exists
$containerExists = docker ps -a --filter "name=qdrant" --format "{{.Names}}"
if ($containerExists -eq "qdrant") {
    Write-Host "Starting existing Qdrant container..." -ForegroundColor Yellow
    docker start qdrant
} else {
    # Start Qdrant
    Write-Host "Starting Qdrant container..." -ForegroundColor Yellow
    docker run -d `
        --name qdrant `
        -p 6333:6333 `
        -p 6334:6334 `
        -v "${PWD}\qdrant_storage:/qdrant/storage" `
        qdrant/qdrant
}

# Wait for Qdrant to be ready
Write-Host "Waiting for Qdrant to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check health
try {
    $health = Invoke-WebRequest -Uri "http://localhost:6333/health" -UseBasicParsing
    if ($health.Content -match "ok") {
        Write-Host "✓ Qdrant is running successfully!" -ForegroundColor Green
        Write-Host "  Health check: http://localhost:6333/health" -ForegroundColor Cyan
        Write-Host "  Dashboard: http://localhost:6333/dashboard" -ForegroundColor Cyan
    }
} catch {
    Write-Host "⚠ Qdrant may not be ready yet. Check with: Invoke-WebRequest http://localhost:6333/health" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "To stop Qdrant: docker stop qdrant" -ForegroundColor Cyan
Write-Host "To remove Qdrant: docker rm qdrant" -ForegroundColor Cyan

