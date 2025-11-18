# PowerShell script to schedule knowledge base updates on Windows
# Run this script as Administrator to set up Task Scheduler

$TaskName = "HygiaAI-Knowledge-Base-Update"
$ScriptPath = Join-Path $PSScriptRoot "update_medical_knowledge_base.py"
# Get project root (parent of scripts directory)
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$PythonExe = (Get-Command python).Source

Write-Host "Setting up Windows Task Scheduler for Knowledge Base Updates" -ForegroundColor Cyan
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "Task already exists. Removing old task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create action
$action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$ScriptPath`"" -WorkingDirectory $ProjectRoot

# Create trigger (every Sunday at 2 AM)
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 2am

# Create settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Create principal (run as current user)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

# Register task
try {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Updates HygiaAI medical knowledge base from internet sources"
    
    Write-Host "✅ Task scheduled successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName"
    Write-Host "  Schedule: Every Sunday at 2:00 AM"
    Write-Host "  Script: $ScriptPath"
    Write-Host ""
    Write-Host "To view the task:" -ForegroundColor Yellow
    Write-Host "  Get-ScheduledTask -TaskName '$TaskName'"
    Write-Host ""
    Write-Host "To run the task manually:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host ""
    Write-Host "To remove the task:" -ForegroundColor Yellow
    Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
    Write-Host ""
    
} catch {
    Write-Host "❌ Error creating task: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure you're running PowerShell as Administrator" -ForegroundColor Yellow
    exit 1
}

