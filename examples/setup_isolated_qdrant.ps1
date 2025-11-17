# Setup Isolated Qdrant Instance for HygiaAI
# This script creates and runs a dedicated Qdrant instance on port 6334

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setting up Isolated Qdrant for HygiaAI" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Stop and remove existing container if it exists
Write-Host ""
Write-Host "Checking for existing container..." -ForegroundColor Yellow
$existing = docker ps -a --filter "name=hygiaai-qdrant" --format "{{.Names}}"
if ($existing -eq "hygiaai-qdrant") {
    Write-Host "⚠️  Found existing container. Stopping and removing..." -ForegroundColor Yellow
    docker stop hygiaai-qdrant 2>$null
    docker rm hygiaai-qdrant 2>$null
    Write-Host "✅ Removed existing container" -ForegroundColor Green
}

# Create and start Qdrant container
Write-Host ""
Write-Host "Starting isolated Qdrant instance..." -ForegroundColor Yellow
Write-Host "  Container name: hygiaai-qdrant" -ForegroundColor Gray
Write-Host "  Port mapping: 6334:6333 (external:internal)" -ForegroundColor Gray
Write-Host "  Data volume: hygiaai-qdrant-data" -ForegroundColor Gray
Write-Host ""

docker run -d `
    --name hygiaai-qdrant `
    -p 6334:6333 `
    -p 6335:6334 `
    -v hygiaai-qdrant-data:/qdrant/storage `
    qdrant/qdrant

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Qdrant container started successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Wait a moment for Qdrant to start
    Write-Host "Waiting for Qdrant to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    # Check if Qdrant is responding
    Write-Host ""
    Write-Host "Verifying Qdrant is running..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:6334/health" -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Qdrant is healthy and responding!" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️  Qdrant is starting but not yet ready. It may take a few more seconds." -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Qdrant Instance Information" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Container Name: hygiaai-qdrant" -ForegroundColor White
    Write-Host "API Endpoint: http://localhost:6334" -ForegroundColor White
    Write-Host "Dashboard: http://localhost:6334/dashboard" -ForegroundColor White
    Write-Host "Data Volume: hygiaai-qdrant-data" -ForegroundColor White
    Write-Host ""
    Write-Host "To use this instance, set in your .env file:" -ForegroundColor Yellow
    Write-Host "  QDRANT_HOST=localhost" -ForegroundColor White
    Write-Host "  QDRANT_PORT=6334" -ForegroundColor White
    Write-Host ""
    Write-Host "Useful commands:" -ForegroundColor Yellow
    Write-Host "  Stop: docker stop hygiaai-qdrant" -ForegroundColor White
    Write-Host "  Start: docker start hygiaai-qdrant" -ForegroundColor White
    Write-Host "  Logs: docker logs hygiaai-qdrant" -ForegroundColor White
    Write-Host "  Remove: docker rm -f hygiaai-qdrant" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "❌ Failed to start Qdrant container" -ForegroundColor Red
    Write-Host "Check Docker logs for errors" -ForegroundColor Yellow
    exit 1
}

