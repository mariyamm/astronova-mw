# 🐳 AstroNova Docker Deployment Guide

This guide covers containerized deployment of the AstroNova astrology platform using Docker and Docker Compose.

## 📋 Prerequisites

- **Docker**: Version 20.10+ 
- **Docker Compose**: Version 2.0+
- **System Requirements**: 
  - Memory: 2GB+ available
  - Disk: 5GB+ free space
  - CPU: 2+ cores recommended

## 🚀 Quick Start (Development)

1. **Clone and setup environment**:
   ```bash
   git clone <your-repo>
   cd AstroNova-f/app
   cp .env.example .env
   ```

2. **Edit your .env file** with your API keys:
   ```bash
   # Required for basic functionality
   OPENAI_API_KEY=your-openai-key
   SHOPIFY_ACCESS_TOKEN=your-shopify-token
   SHOPIFY_SHOP_URL=your-store.myshopify.com
   ```

3. **Start development environment**:
   ```bash
   # Using Docker Compose directly
   docker-compose up -d
   
   # OR using the build script (Bash/Linux/Mac)
   ./docker-build.sh dev
   
   # OR using PowerShell (Windows)
   .\docker-build.ps1 dev
   ```

4. **Access the application**:
   - **Web UI**: http://localhost:8000
   - **Health Check**: http://localhost:8000/api/admin/health
   - **API Docs**: http://localhost:8000/docs

## 📁 File Structure

```
app/
├── 🐳 Docker Configuration
│   ├── Dockerfile              # Production API image
│   ├── Dockerfile.dev          # Development API image  
│   ├── Dockerfile.worker       # Production worker image
│   ├── Dockerfile.worker.dev   # Development worker image
│   ├── .dockerignore           # Build optimization
│   ├── docker-compose.yml      # Development setup
│   ├── docker-compose.prod.yml # Production setup
│   └── nginx.conf              # Reverse proxy config
│
├── 🔧 Build & Monitoring Scripts
│   ├── docker-build.sh         # Unix build script
│   ├── docker-build.ps1        # Windows build script
│   ├── worker-monitor.sh       # Unix worker monitoring
│   └── worker-monitor.ps1      # Windows worker monitoring
│
├── ⚙️ Environment Configuration
│   ├── .env.example            # Template with all variables
│   ├── .env                    # Your local config (create this)
│   └── .env.production         # Production config (for prod deploy)
│
└── 📱 Application Code
    ├── main.py                 # FastAPI application
    ├── requirements.txt        # Python dependencies
    └── ...
```

## 🔧 Docker Images

### API Images
- **Development** (`Dockerfile.dev`): Hot reload, debug logging, development tools
- **Production** (`Dockerfile`): Optimized, secure, non-root user

### Worker Images  
- **Development** (`Dockerfile.worker.dev`): Single worker, verbose logging, development tools
- **Production** (`Dockerfile.worker`): Optimized for PDF generation, memory management

**Key Worker Optimizations**:
- ✅ Specialized system dependencies for PDF generation
- ✅ Memory management settings for long-running processes
- ✅ Font support for Bulgarian (Cyrillic) text
- ✅ Health checks specific to Celery workers
- ✅ Resource limits to prevent memory leaks

## 📦 Services Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Nginx     │  │  FastAPI    │  │   Celery    │     │
│  │ (optional)  │◄─┤    API      │  │   Worker    │     │
│  │   :80/443   │  │   :8000     │  │ (background)│     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│         │               │                  │           │
│         └───────────────┼──────────────────┘           │
│                         │                              │
│  ┌─────────────┐  ┌─────────────┐                      │
│  │ PostgreSQL  │  │   Redis     │                      │
│  │   :5432     │  │   :6379     │                      │
│  └─────────────┘  └─────────────┘                      │
└─────────────────────────────────────────────────────────┘
```

**Service Descriptions**:
- **api**: Main FastAPI application server (uses `Dockerfile` / `Dockerfile.dev`)
- **celery_worker**: Background PDF generation worker (uses `Dockerfile.worker` / `Dockerfile.worker.dev`)
- **db**: PostgreSQL database for application data
- **redis**: Task queue and caching layer for Celery
- **nginx** *(production)*: Reverse proxy and SSL termination

## 🌍 Environment Configurations

### Development Environment
- **Hot reload**: Code changes trigger automatic restarts
- **Exposed ports**: Database and Redis accessible for debugging
- **Logging**: Debug level logging enabled
- **Volumes**: Source code mounted for live editing

### Production Environment
- **Security**: Services run as non-root users
- **Networks**: Internal communication only (no exposed DB ports)
- **SSL**: Nginx handles HTTPS termination
- **Resource limits**: Memory and CPU constraints
- **Health checks**: Automated service monitoring

## 🔐 Security Configuration

### Required Environment Variables
```bash
# Application Security
SECRET_KEY=<generate-strong-random-key>

# Database (Production)
POSTGRES_PASSWORD=<strong-database-password>

# Redis (Production) 
REDIS_PASSWORD=<redis-password>

# External APIs
OPENAI_API_KEY=sk-...
SHOPIFY_ACCESS_TOKEN=shpat_...
TIMEZONEDB_API_KEY=...
```

### Security Features
- **Non-root containers**: All services run with restricted privileges
- **Network isolation**: Internal Docker network for service communication
- **Secrets management**: Environment variables for sensitive data
- **HTTPS support**: SSL/TLS termination via Nginx
- **Rate limiting**: API rate limits configured in Nginx

## 🚀 Deployment Commands

### Development Deployment
```bash
# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build -d
```

### Production Deployment
```bash
# 1. Prepare production environment
cp .env.example .env.production
# Edit .env.production with production values

# 2. Build production images
./docker-build.sh prod

# 3. Start production services
docker-compose -f docker-compose.prod.yml up -d

# 4. Check service health
docker-compose -f docker-compose.prod.yml ps
curl http://localhost:8000/api/admin/health
```

### Build Scripts Usage
```bash
# Development build and start
./docker-build.sh dev

# Production build with version tag
./docker-build.sh prod v1.2.3

# Windows PowerShell
.\docker-build.ps1 dev
.\docker-build.ps1 prod v1.2.3
```

## 🔍 Monitoring and Debugging

### Health Checks
```bash
# Application health
curl http://localhost:8000/api/admin/health

# Service status
docker-compose ps

# Container logs
docker-compose logs api
docker-compose logs celery_worker
docker-compose logs db
```

### Performance Monitoring
```bash
# Resource usage
docker stats

# Service specific stats
docker stats astronova_api
docker stats astronova_celery
```

### Troubleshooting
```bash
# Enter container shell
docker exec -it astronova_api bash

# Database connection test
docker exec -it astronova_db psql -U postgres -d astronova

# Redis connection test
docker exec -it astronova_redis redis-cli ping

# View all container logs
docker-compose logs --tail=100 -f
```

### Worker Monitoring
```bash
# Check worker status (Unix/Linux/Mac)
./worker-monitor.sh status

# Check worker status (Windows)
.\worker-monitor.ps1 status

# View worker logs
./worker-monitor.sh logs

# Restart worker if stuck
./worker-monitor.sh restart

# Clear failed tasks from queue
./worker-monitor.sh clear

# Detailed worker inspection
./worker-monitor.sh inspect
```

**Worker Health Checks**:
- **Container health**: Automatic Docker health checks every 60s
- **Celery ping**: Worker responsiveness to management commands  
- **Memory usage**: Automatic worker recycling after 512MB (production)
- **Task monitoring**: Active and scheduled task inspection

## 📊 Scaling and Performance

### Horizontal Scaling
```yaml
# In docker-compose.yml, scale Celery workers:
celery_worker:
  deploy:
    replicas: 3  # Run 3 worker instances
```

### Resource Optimization
```yaml
# Adjust resource limits in production
api:
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: '0.5'
      reservations:
        memory: 512M
        cpus: '0.25'
```

### Performance Tips
- **Database**: Use connection pooling (already configured)
- **Redis**: Tune maxmemory policy for your use case
- **Celery**: Adjust concurrency based on CPU cores
- **Nginx**: Enable gzip compression (already configured)

## 🆘 Common Issues

### Port Conflicts
```bash
# Check what's using port 8000
netstat -tulpn | grep :8000
# Kill conflicting processes or change PORT in .env
```

### Database Connection Issues  
```bash
# Reset database
docker-compose down -v
docker-compose up -d db
# Wait for DB to initialize, then start other services
```

### Memory Issues
```bash
# Clear Docker system cache
docker system prune -a
# Increase available memory or tune resource limits
```

### SSL Certificate Setup (Production)
```bash
# Place certificates in ssl/ directory
mkdir ssl/
cp your-domain.crt ssl/cert.pem
cp your-domain.key ssl/key.pem
# Uncomment HTTPS server block in nginx.conf
```

## 📚 Additional Resources

- **Docker Documentation**: https://docs.docker.com/
- **Docker Compose Reference**: https://docs.docker.com/compose/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **PostgreSQL Docker**: https://hub.docker.com/_/postgres
- **Redis Docker**: https://hub.docker.com/_/redis

## 🤝 Contributing

When contributing to the Docker configuration:

1. Test changes in development environment first
2. Update both `Dockerfile` and `Dockerfile.dev` if needed  
3. Update this README if you add new features
4. Ensure build scripts work on both Unix and Windows
5. Test production deployment in staging environment

---

**Need Help?** Create an issue in the repository with:
- Your operating system
- Docker version (`docker --version`)
- Error messages or logs
- Steps to reproduce the issue