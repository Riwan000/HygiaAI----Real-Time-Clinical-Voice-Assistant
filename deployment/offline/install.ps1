# HygiaAI Offline Rural Deployment Kit - Windows Installation Script
# This script sets up HygiaAI for offline deployment in rural environments

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "HygiaAI Offline Deployment Kit" -ForegroundColor Cyan
Write-Host "Windows Installation Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Warning: Not running as Administrator. Some operations may require elevation." -ForegroundColor Yellow
}

# Function to check if command exists
function Test-Command {
    param($CommandName)
    $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow
$MissingDeps = @()

if (-not (Test-Command "docker")) {
    $MissingDeps += "docker"
}

if (-not (Test-Command "docker-compose")) {
    $MissingDeps += "docker-compose"
}

if ($MissingDeps.Count -gt 0) {
    Write-Host "Error: Missing required dependencies: $($MissingDeps -join ', ')" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Docker Desktop for Windows:"
    Write-Host "  Download from: https://www.docker.com/products/docker-desktop"
    Write-Host "  Or use Chocolatey: choco install docker-desktop"
    exit 1
}

Write-Host "✓ All prerequisites met" -ForegroundColor Green
Write-Host ""

# Get installation directory
$InstallDir = if ($args[0]) { $args[0] } else { "C:\HygiaAI" }
Write-Host "Installation directory: $InstallDir"

# Create installation directory
Write-Host "Creating installation directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

# Copy deployment files
Write-Host "Copying deployment files..." -ForegroundColor Yellow
Copy-Item -Path "deployment\offline\*" -Destination $InstallDir -Recurse -Force
if (Test-Path "docker-compose.yml") {
    Copy-Item -Path "docker-compose.yml" -Destination $InstallDir -Force
}

# Create necessary directories
Write-Host "Creating data directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "$InstallDir\data" | Out-Null
New-Item -ItemType Directory -Force -Path "$InstallDir\logs" | Out-Null
New-Item -ItemType Directory -Force -Path "$InstallDir\config" | Out-Null

# Set up environment file
if (-not (Test-Path "$InstallDir\.env.offline")) {
    Write-Host "Creating environment configuration..." -ForegroundColor Yellow
    if (Test-Path "$InstallDir\env.offline.example") {
        Copy-Item -Path "$InstallDir\env.offline.example" -Destination "$InstallDir\.env.offline"
    } elseif (Test-Path "$InstallDir\.env.offline.example") {
        Copy-Item -Path "$InstallDir\.env.offline.example" -Destination "$InstallDir\.env.offline"
    }
    Write-Host "Please edit $InstallDir\.env.offline with your configuration" -ForegroundColor Yellow
}

# Pull Docker images (if internet available)
try {
    $ping = Test-NetConnection -ComputerName 8.8.8.8 -Port 53 -WarningAction SilentlyContinue
    if ($ping.TcpTestSucceeded) {
        Write-Host "Pulling Docker images..." -ForegroundColor Yellow
        Set-Location $InstallDir
        docker-compose pull
    } else {
        Write-Host "No internet connection detected. Using local Docker images." -ForegroundColor Yellow
    }
} catch {
    Write-Host "No internet connection detected. Using local Docker images." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Installation completed successfully!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Edit configuration: $InstallDir\.env.offline"
Write-Host "2. Start services: Set-Location $InstallDir; .\start.ps1"
Write-Host "3. Check health: Set-Location $InstallDir; .\health-check.ps1"
Write-Host ""
Write-Host "Access the application at:"
Write-Host "  Frontend: http://localhost:3000"
Write-Host "  Backend API: http://localhost:8000"
Write-Host "  API Docs: http://localhost:8000/docs"
Write-Host "  Qdrant Dashboard: http://localhost:6333/dashboard"
Write-Host ""

