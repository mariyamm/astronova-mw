# AstroNova Docker Build and Deployment Script (PowerShell)
# Usage: .\docker-build.ps1 [dev|prod] [version]

param(
    [Parameter(Position=0)]
    [ValidateSet("dev", "prod")]
    [string]$Environment = "dev",
    
    [Parameter(Position=1)]
    [string]$Version = "latest"
)

$ErrorActionPreference = "Stop"
$ImageName = "astronova"

Write-Host "🐳 Building AstroNova Docker images for environment: $Environment" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Function to build and tag image
function Build-Image {
    param($Dockerfile, $Tag)
    
    Write-Host "📦 Building $Tag..." -ForegroundColor Yellow
    docker build -f $Dockerfile -t "${ImageName}:$Tag" .
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully built $Tag" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to build $Tag" -ForegroundColor Red
        exit 1
    }
}

# Clean up old images
Write-Host "🧹 Cleaning up old images..." -ForegroundColor Yellow
docker image prune -f | Out-Null

if ($Environment -eq "dev") {
    Write-Host "🔨 Building development images..." -ForegroundColor Blue
    
    # Build development images
    Build-Image "Dockerfile.dev" "api-dev"
    Build-Image "Dockerfile.worker.dev" "worker-dev"
    
    # Tag with version
    docker tag "${ImageName}:api-dev" "${ImageName}:api-dev-$Version"
    docker tag "${ImageName}:worker-dev" "${ImageName}:worker-dev-$Version"
    
    Write-Host "🚀 Starting development environment..." -ForegroundColor Yellow
    docker-compose down 2>$null
    docker-compose up --build -d
    
    Write-Host "✅ Development environment is running!" -ForegroundColor Green
    Write-Host "🌐 API: http://localhost:8000" -ForegroundColor White
    Write-Host "🔍 Health check: http://localhost:8000/api/admin/health" -ForegroundColor White
    Write-Host "📊 Logs: docker-compose logs -f" -ForegroundColor White
    Write-Host "🔧 Worker queue monitor: docker exec -it astronova_celery celery -A services.pdf_tasks inspect active" -ForegroundColor White
    
} elseif ($Environment -eq "prod") {
    Write-Host "🏭 Building production images..." -ForegroundColor Blue
    
    # Build production images
    Build-Image "Dockerfile" "api-prod"
    Build-Image "Dockerfile.worker" "worker-prod"
    
    # Tag with version
    docker tag "${ImageName}:api-prod" "${ImageName}:api-prod-$Version"
    docker tag "${ImageName}:worker-prod" "${ImageName}:worker-prod-$Version"
    docker tag "${ImageName}:api-prod" "${ImageName}:latest"
    
    Write-Host "✅ Production images built successfully!" -ForegroundColor Green
    Write-Host "📦 Images:" -ForegroundColor White
    Write-Host "   - ${ImageName}:api-prod" -ForegroundColor Gray
    Write-Host "   - ${ImageName}:worker-prod" -ForegroundColor Gray
    Write-Host "   - ${ImageName}:latest" -ForegroundColor Gray
    Write-Host "   - ${ImageName}:api-prod-$Version" -ForegroundColor Gray
    Write-Host "   - ${ImageName}:worker-prod-$Version" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🚀 To start production environment:" -ForegroundColor Yellow
    Write-Host "   docker-compose -f docker-compose.prod.yml up -d" -ForegroundColor White
    Write-Host ""
    Write-Host "🔒 Remember to:" -ForegroundColor Red
    Write-Host "   1. Create .env.production with your secrets" -ForegroundColor White
    Write-Host "   2. Setup SSL certificates in .\ssl\" -ForegroundColor White
    Write-Host "   3. Configure your domain in nginx.conf" -ForegroundColor White
}

Write-Host ""
Write-Host "🐳 Docker images:" -ForegroundColor Cyan
docker images | Select-String $ImageName | Select-Object -First 5

Write-Host ""
Write-Host "📋 Container status:" -ForegroundColor Cyan
$containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String "astronova"
if ($containers) {
    $containers
} else {
    Write-Host "No AstroNova containers running" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🎉 Build complete!" -ForegroundColor Green