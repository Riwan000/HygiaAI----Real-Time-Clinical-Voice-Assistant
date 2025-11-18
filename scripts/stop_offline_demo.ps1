# Stop HygiaAI Offline Demo Services

Write-Host "Stopping HygiaAI demo services..."

# Stop Qdrant
Write-Host "Stopping Qdrant..."
docker stop hygiaai-qdrant 2>$null

# Note: Backend and Frontend windows need to be closed manually
Write-Host ""
Write-Host "Note: Please close the backend and frontend PowerShell windows manually."
Write-Host "✓ Qdrant stopped"

