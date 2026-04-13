import sys
import os

# Ensure the app directory is on the Python path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="AstroNova API",
    description="AstroNova Application API with User Management",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint - basic health check"""
    return {"message": "AstroNova API is running", "status": "healthy"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "astronova-api"}

@app.get("/api/admin/health")
async def admin_health():
    """Admin health check endpoint"""
    return {"status": "healthy", "service": "astronova-api", "admin": True}

# Import and include routers with error handling
try:
    print("Attempting to import API routers...")
    
    from api.auth import router as auth_router
    app.include_router(auth_router)
    print("✅ Auth router loaded")
    
    from api.users import router as users_router  
    app.include_router(users_router)
    print("✅ Users router loaded")
    
    from api.permissions import router as permissions_router
    app.include_router(permissions_router)
    print("✅ Permissions router loaded")
    
    from api.admin import router as admin_router
    app.include_router(admin_router)
    print("✅ Admin router loaded")
    
    from api.shopify import router as shopify_router
    app.include_router(shopify_router)
    print("✅ Shopify router loaded")
    
except Exception as e:
    print(f"⚠️  Warning: Could not load some API routers: {e}")
    import traceback
    traceback.print_exc()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)