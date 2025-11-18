# PowerShell script to run WebSocket proxy tests

Write-Host "🧪 Running WebSocket Proxy Tests" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# Check if pytest is installed
try {
    $null = Get-Command pytest -ErrorAction Stop
} catch {
    Write-Host "❌ pytest not found. Installing..." -ForegroundColor Yellow
    pip install pytest pytest-asyncio pytest-cov
}

# Run unit tests
Write-Host ""
Write-Host "📋 Running Unit Tests (Mocked)..." -ForegroundColor Green
pytest tests/test_websocket_proxy.py -v --tb=short

# Check if backend is running for integration tests
Write-Host ""
Write-Host "🔍 Checking if backend is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/transcription/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✅ Backend is running. Running integration tests..." -ForegroundColor Green
    pytest tests/test_websocket_proxy_integration.py -v -m integration --tb=short
} catch {
    Write-Host "⚠️  Backend not running. Skipping integration tests." -ForegroundColor Yellow
    Write-Host "   To run integration tests, start the backend server first:" -ForegroundColor Yellow
    Write-Host "   uvicorn src.main:app --reload" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Test run complete!" -ForegroundColor Green

