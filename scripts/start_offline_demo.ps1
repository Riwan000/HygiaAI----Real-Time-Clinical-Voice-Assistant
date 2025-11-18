#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start HygiaAI for offline/rural demo

.DESCRIPTION
    Starts all required services for offline demonstration:
    - Qdrant vector database
    - Backend API server
    - Frontend development server

.EXAMPLE
    .\scripts\start_offline_demo.ps1
#>

Write-Host "=" * 80
Write-Host "  HygiaAI Offline Demo Startup"
Write-Host "=" * 80
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..."
try {
    docker ps | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Start Qdrant
Write-Host ""
Write-Host "Starting Qdrant vector database..."
$qdrantRunning = docker ps --filter "name=hygiaai-qdrant" --format "{{.Names}}"
if ($qdrantRunning -eq "hygiaai-qdrant") {
    Write-Host "✓ Qdrant is already running" -ForegroundColor Green
} else {
    # Check if container exists
    $qdrantExists = docker ps -a --filter "name=hygiaai-qdrant" --format "{{.Names}}"
    if ($qdrantExists -eq "hygiaai-qdrant") {
        docker start hygiaai-qdrant | Out-Null
        Write-Host "✓ Qdrant container started" -ForegroundColor Green
    } else {
        Write-Host "Creating Qdrant container..."
        docker run -d `
            -p 6334:6333 `
            -p 6335:6334 `
            --name hygiaai-qdrant `
            -v hygiaai-qdrant-data:/qdrant/storage `
            qdrant/qdrant | Out-Null
        Write-Host "✓ Qdrant container created and started" -ForegroundColor Green
    }
}

# Wait for Qdrant to be ready
Write-Host "Waiting for Qdrant to be ready..."
$maxAttempts = 30
$attempt = 0
$qdrantReady = $false

while ($attempt -lt $maxAttempts -and -not $qdrantReady) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:6334/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $qdrantReady = $true
            Write-Host "✓ Qdrant is ready" -ForegroundColor Green
        }
    } catch {
        $attempt++
        Start-Sleep -Seconds 1
        Write-Host "." -NoNewline
    }
}

if (-not $qdrantReady) {
    Write-Host ""
    Write-Host "⚠ Qdrant may not be ready yet, but continuing..." -ForegroundColor Yellow
}

# Check if backend is already running
Write-Host ""
Write-Host "Checking backend server..."
try {
    $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ Backend is already running" -ForegroundColor Green
} catch {
    Write-Host "Starting backend server..."
    Write-Host "  (Backend will run in a new window)" -ForegroundColor Gray
    
    # Start backend in new window
    $backendScript = @"
cd '$PWD'
python run_server.py
pause
"@
    
    $tempScript = [System.IO.Path]::GetTempFileName() + ".ps1"
    $backendScript | Out-File -FilePath $tempScript -Encoding UTF8
    
    Start-Process powershell -ArgumentList "-NoExit", "-File", $tempScript
    Write-Host "✓ Backend server starting..." -ForegroundColor Green
    Start-Sleep -Seconds 3
}

# Check if frontend is already running
Write-Host ""
Write-Host "Checking frontend server..."
try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ Frontend is already running" -ForegroundColor Green
} catch {
    Write-Host "Starting frontend server..."
    Write-Host "  (Frontend will run in a new window)" -ForegroundColor Gray
    
    # Start frontend in new window
    $frontendScript = @"
cd '$PWD\frontend'
npm run dev
pause
"@
    
    $tempScript = [System.IO.Path]::GetTempFileName() + ".ps1"
    $frontendScript | Out-File -FilePath $tempScript -Encoding UTF8
    
    Start-Process powershell -ArgumentList "-NoExit", "-File", $tempScript
    Write-Host "✓ Frontend server starting..." -ForegroundColor Green
    Start-Sleep -Seconds 5
}

# Summary
Write-Host ""
Write-Host "=" * 80
Write-Host "  Demo Ready!"
Write-Host "=" * 80
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
Write-Host "  • Qdrant:     http://localhost:6334" -ForegroundColor White
Write-Host "  • Backend:    http://localhost:8000" -ForegroundColor White
Write-Host "  • Frontend:   http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Open your browser to: http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to open browser..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Open browser
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "Demo is running! Close this window to stop." -ForegroundColor Green
Write-Host ""

