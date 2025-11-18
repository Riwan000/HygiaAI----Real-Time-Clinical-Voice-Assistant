# Stop HygiaAI Offline Deployment

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "Stopping HygiaAI services..." -ForegroundColor Yellow

docker-compose down

Write-Host "Services stopped." -ForegroundColor Green

