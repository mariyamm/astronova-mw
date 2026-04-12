# AstroNova Admin Setup Script
# This script will set up the AstroNova admin system

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   AstroNova Admin System Setup   " -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Cyan
try {
    docker ps | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Start Docker containers
Write-Host "Starting Docker containers..." -ForegroundColor Cyan
docker compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Docker containers started successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to start Docker containers" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Wait for database to be ready
Write-Host "Waiting for database to be ready..." -ForegroundColor Cyan
Start-Sleep -Seconds 5
Write-Host "✓ Database should be ready" -ForegroundColor Green

Write-Host ""

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Cyan
python init_db.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Database initialized successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to initialize database" -ForegroundColor Red
    Write-Host "  Tip: Make sure PostgreSQL is accessible" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Setup Complete!   " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Default Admin Credentials:" -ForegroundColor Yellow
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: admin123" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  IMPORTANT: Change the password after first login!" -ForegroundColor Red
Write-Host ""
Write-Host "To start the server, run:" -ForegroundColor Cyan
Write-Host "  uvicorn main:app --reload" -ForegroundColor White
Write-Host ""
Write-Host "Then open your browser at:" -ForegroundColor Cyan
Write-Host "  http://localhost:8000/" -ForegroundColor White
Write-Host ""
