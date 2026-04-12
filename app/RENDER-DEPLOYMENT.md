# 🚀 AstroNova Render.com Deployment Guide

Complete guide for deploying AstroNova to Render.com cloud platform.

## 📋 Prerequisites

- **GitHub Account**: Repository must be hosted on GitHub
- **Render Account**: Sign up at [render.com](https://render.com)
- **API Keys**: OpenAI, Shopify, TimezoneDB, Google Drive credentials

## 🎯 Quick Deployment

### **Step 1: Prepare Repository**

1. **Fork or push your repository to GitHub**
2. **Ensure render.yaml is in the root directory** ✅ (already configured)
3. **Verify Docker files exist in app/ directory** ✅

### **Step 2: Create Render Blueprint**

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click "New" → "Blueprint"**
3. **Connect your GitHub repository**
4. **Render will automatically detect the `render.yaml`**
5. **Click "Apply"**

### **Step 3: Configure Environment Variables**

After deployment, you'll need to set these environment variables in the Render dashboard:

#### **🔑 Required API Keys**
```bash
# OpenAI (for report generation)
OPENAI_API_KEY=sk-your-openai-key-here

# Astrology API (for chart calculations)
ASTROLOGY_API_KEY=ask_your-astrology-api-key-here

# Shopify (for order sync)
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_your-access-token
SHOPIFY_WEBHOOK_SECRET=your-webhook-secret

# TimezoneDB (for timezone calculations)
TIMEZONEDB_API_KEY=your-timezonedb-key

# Google Drive (for PDF storage)
GDRIVE_CLIENT_JSON={"web":{"client_id":"...","client_secret":"..."}}
GDRIVE_TOKEN_JSON={"token":"...","refresh_token":"..."}
```

#### **⚡ How to Set Variables**
1. **Go to your service** (astronova-api or astronova-worker)
2. **Click "Environment"**
3. **Add each variable from the list above**
4. **Save and redeploy**

## 📊 Service Architecture

Your deployment includes these services:

```
┌─────────────────────────────────────────────────────┐
│                 Render.com Cloud                    │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   Web App   │  │   Worker    │  │   Redis     │ │
│  │(FastAPI API)│  │  (Celery)   │  │  (Cache)    │ │
│  │    :443     │  │ (PDF Tasks) │  │   :6379     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
│         │                 │               │       │
│         └─────────────────┼───────────────┘       │
│                           │                       │
│              ┌─────────────────────────┐           │
│              │     PostgreSQL DB       │           │
│              │        :5432           │           │
│              └─────────────────────────┘           │
└─────────────────────────────────────────────────────┘
```

### **Service Details**

| Service | Type | Purpose | Auto Scaling |
|---------|------|---------|--------------|
| **astronova-api** | Web | FastAPI application | 1-3 instances |
| **astronova-worker** | Worker | PDF generation | 1-2 instances |  
| **astronova-redis** | Redis | Task queue & cache | Managed |
| **astronova-db** | PostgreSQL | Data storage | Managed |

## 🔒 Security Configuration

### **Environment Variables**
- ✅ **Secrets marked `sync: false`** - Set manually in dashboard
- ✅ **SECRET_KEY auto-generated** - JWT token security
- ✅ **DATABASE_URL auto-configured** - Secure connection strings
- ✅ **CORS configured for production** - Only allow your domain

### **Docker Security**
- ✅ **Non-root users** in containers
- ✅ **Health checks** for monitoring
- ✅ **Resource limits** prevent abuse

## 📈 Monitoring & Health Checks

### **Built-in Monitoring**
- **Health Check**: `https://your-app.onrender.com/api/admin/health`
- **Logs**: Available in Render dashboard
- **Metrics**: CPU, Memory, Request count
- **Alerts**: Configure in Render settings

### **Worker Monitoring** 
To enable Celery monitoring, uncomment the Flower service in `render.yaml`:
```yaml
# Uncomment this section for worker monitoring
- type: web
  name: astronova-monitor
  runtime: docker
  # ... (Flower configuration)
```

### **Manual Checks**
```bash
# Test API health
curl https://your-app.onrender.com/api/admin/health

# Check logs
# Go to Render dashboard → Service → Logs
```

## 💰 Cost Optimization

### **Starter Configuration** (Recommended)
| Resource | Plan | Monthly Cost | Notes |
|----------|------|--------------|--------|
| **API Server** | Starter | $7 | Auto-scales 1-3 instances |
| **Worker** | Starter | $7 | Auto-scales 1-2 workers |
| **PostgreSQL** | Starter | $7 | 1GB storage, backups |
| **Redis** | Starter | $7 | 25MB cache |
| **Storage** | 2GB each | $0.10 | PDF file storage |
| **Total** | | **~$28/month** | Production ready |

### **Free Tier** (Development)
- Change all plans to `free` in `render.yaml`
- **Limitations**: 
  - Services spin down after 15 min of inactivity
  - Limited storage and bandwidth
  - No auto-scaling

### **Scaling Rules**
```yaml
# In render.yaml, adjust scaling:
scaling:
  minInstances: 1      # Always-on instances
  maxInstances: 5      # Scale up to this limit
```

## 🚀 Deployment Steps

### **1. Initial Deployment**
1. **Create Blueprint** with your GitHub repo
2. **Services will build** (5-10 minutes)
3. **Set environment variables** (see list above)
4. **Redeploy services** after setting variables

### **2. Post-Deployment Setup**
```bash
# 1. Test API connectivity
curl https://your-app.onrender.com/api/admin/health

# 2. Create admin user (run once)
# Go to astronova-api → Shell
python -c "
from db.database import SessionLocal
from models.user import User
from core.security import get_password_hash
db = SessionLocal()
admin = User(
    username='admin',
    email='admin@astronova.com',
    hashed_password=get_password_hash('your-password'),
    role='admin',
    is_active=True
)
db.add(admin)
db.commit()
print('Admin user created!')
"

# 3. Test Shopify webhook
# Configure webhook URL in Shopify:
# https://your-app.onrender.com/api/shopify/webhooks/orders/create
```

### **3. Configure Webhook in Shopify**
1. **Go to Shopify Admin** → Settings → Notifications
2. **Create webhook**:
   - **Event**: Order creation
   - **URL**: `https://your-app.onrender.com/api/shopify/webhooks/orders/create`
   - **Format**: JSON
3. **Add webhook secret** to `SHOPIFY_WEBHOOK_SECRET` env var

## 🛠️ Troubleshooting

### **Common Issues**

#### **Build Failures**
```bash
# Check build logs in Render dashboard
# Common fixes:
- Ensure Dockerfile.worker exists in app/
- Check requirements.txt syntax
- Verify environment variables
```

#### **Worker Not Processing Tasks**
```bash
# Check worker logs
# Common fixes:
1. Verify Redis connection
2. Check OPENAI_API_KEY is set
3. Ensure worker has access to shared storage
```

#### **Database Connection Issues**
```bash
# Auto-resolved by Render
# DATABASE_URL is automatically configured
# Check service dependencies in dashboard
```

#### **PDF Generation Fails**
```bash
# Check worker logs for font/library issues
# WeasyPrint dependencies are included in Dockerfile.worker
# Verify GDRIVE credentials for PDF uploads
```

### **Performance Optimization**

#### **Scaling Triggers**
```yaml
# Optimize auto-scaling in render.yaml
scaling:
  minInstances: 1
  maxInstances: 3
# Scale based on:
# - Response time > 1000ms
# - CPU usage > 80%
# - Memory usage > 85%
```

#### **Worker Optimization**
```bash
# Adjust concurrency based on performance
startCommand: celery -A services.pdf_tasks worker --concurrency=4
# Monitor memory usage and adjust max-tasks-per-child
```

## 📚 Additional Resources

- **Render Documentation**: https://render.com/docs
- **Blueprint Spec**: https://render.com/docs/blueprint-spec  
- **Docker Support**: https://render.com/docs/docker
- **Environment Variables**: https://render.com/docs/environment-variables
- **Monitoring**: https://render.com/docs/monitoring-sla

## ✅ Production Checklist

### **Pre-Launch**
- [ ] All environment variables configured
- [ ] API health check responds correctly
- [ ] Worker processing test PDFs
- [ ] Shopify webhook receiving orders
- [ ] Database migrations applied
- [ ] Admin user created

### **Security**
- [ ] Strong SECRET_KEY generated
- [ ] API keys properly secured
- [ ] CORS configured for your domain
- [ ] Webhook secrets configured
- [ ] SSL/HTTPS enabled (automatic)

### **Monitoring**
- [ ] Health checks configured
- [ ] Log monitoring enabled
- [ ] Performance alerts set up
- [ ] Backup verification
- [ ] Scaling rules tested

### **Performance**
- [ ] Load testing completed
- [ ] PDF generation time monitored
- [ ] Auto-scaling tested
- [ ] Resource usage optimized
- [ ] CDN configured (if needed)

---

**🎉 Your AstroNova application is now production-ready on Render.com!**

For support, check the [Render documentation](https://render.com/docs) or create an issue in your repository.