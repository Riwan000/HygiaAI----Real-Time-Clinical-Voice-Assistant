# Test Deepgram API Key validity (PowerShell)
# Usage: .\test_deepgram_key.ps1 YOUR_API_KEY

param(
    [string]$ApiKey = "your_api_key_here"
)

if ($ApiKey -eq "your_api_key_here") {
    Write-Host "Usage: .\test_deepgram_key.ps1 -ApiKey YOUR_API_KEY" -ForegroundColor Yellow
    exit 1
}

Write-Host "Testing Deepgram API Key..." -ForegroundColor Cyan
Write-Host "API Key: $($ApiKey.Substring(0, [Math]::Min(10, $ApiKey.Length)))..." -ForegroundColor Gray

try {
    $headers = @{
        "Authorization" = "Token $ApiKey"
        "Content-Type" = "application/json"
    }
    
    $response = Invoke-RestMethod -Uri "https://api.deepgram.com/v1/projects" -Method Get -Headers $headers
    
    Write-Host "✅ API Key is VALID!" -ForegroundColor Green
    Write-Host "Projects found: $($response.projects.Count)" -ForegroundColor Green
} catch {
    Write-Host "❌ API Key is INVALID or has no access" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nCheck:" -ForegroundColor Yellow
    Write-Host "1. API key is correct at https://console.deepgram.com/" -ForegroundColor White
    Write-Host "2. API key has WebSocket/Live transcription permissions" -ForegroundColor White
    Write-Host "3. Account is active and has credits" -ForegroundColor White
}

