#!/bin/bash

# AstroNova Docker Build and Deployment Script
# Usage: ./docker-build.sh [dev|prod]

set -e  # Exit on any error

ENV=${1:-dev}
IMAGE_NAME="astronova"
VERSION=${2:-latest}

echo "🐳 Building AstroNova Docker images for environment: $ENV"
echo "=================================================="

# Function to build and tag image
build_image() {
    local dockerfile=$1
    local tag=$2
    
    echo "📦 Building $tag..."
    docker build -f $dockerfile -t $IMAGE_NAME:$tag .
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully built $tag"
    else
        echo "❌ Failed to build $tag"
        exit 1
    fi
}

# Clean up old images
echo "🧹 Cleaning up old images..."
docker image prune -f

if [ "$ENV" = "dev" ]; then
    echo "🔨 Building development images..."
    
    # Build development images
    build_image "Dockerfile.dev" "api-dev"
    build_image "Dockerfile.worker.dev" "worker-dev"
    
    # Tag with version
    docker tag $IMAGE_NAME:api-dev $IMAGE_NAME:api-dev-$VERSION
    docker tag $IMAGE_NAME:worker-dev $IMAGE_NAME:worker-dev-$VERSION
    
    echo "🚀 Starting development environment..."
    docker-compose down
    docker-compose up --build -d
    
    echo "✅ Development environment is running!"
    echo "🌐 API: http://localhost:8000"
    echo "🔍 Health check: http://localhost:8000/api/admin/health"
    echo "📊 Logs: docker-compose logs -f"
    echo "🔧 Worker queue monitor: docker exec -it astronova_celery celery -A services.pdf_tasks inspect active"
    
elif [ "$ENV" = "prod" ]; then
    echo "🏭 Building production images..."
    
    # Build production images
    build_image "Dockerfile" "api-prod"
    build_image "Dockerfile.worker" "worker-prod"
    
    # Tag with version
    docker tag $IMAGE_NAME:api-prod $IMAGE_NAME:api-prod-$VERSION
    docker tag $IMAGE_NAME:worker-prod $IMAGE_NAME:worker-prod-$VERSION
    docker tag $IMAGE_NAME:api-prod $IMAGE_NAME:latest
    
    echo "✅ Production images built successfully!"
    echo "📦 Images:"
    echo "   - $IMAGE_NAME:api-prod"
    echo "   - $IMAGE_NAME:worker-prod"
    echo "   - $IMAGE_NAME:latest"
    echo "   - $IMAGE_NAME:api-prod-$VERSION"
    echo "   - $IMAGE_NAME:worker-prod-$VERSION"
    echo ""
    echo "🚀 To start production environment:"
    echo "   docker-compose -f docker-compose.prod.yml up -d"
    echo ""
    echo "🔒 Remember to:"
    echo "   1. Create .env.production with your secrets"
    echo "   2. Setup SSL certificates in ./ssl/"
    echo "   3. Configure your domain in nginx.conf"

else
    echo "❌ Invalid environment: $ENV"
    echo "Usage: $0 [dev|prod] [version]"
    echo "Examples:"
    echo "  $0 dev"
    echo "  $0 prod v1.0.0"
    exit 1
fi

echo ""
echo "🐳 Docker images:"
docker images | grep $IMAGE_NAME | head -5

echo ""
echo "📋 Container status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep astronova || echo "No AstroNova containers running"

echo ""
echo "🎉 Build complete!"