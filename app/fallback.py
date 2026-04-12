from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Ultra-minimal FastAPI app with no external dependencies
app = FastAPI(title="AstroNova Fallback", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "AstroNova API (fallback mode)", "status": "minimal"}

@app.get("/health")  
async def health():
    return {"status": "healthy", "mode": "fallback"}

@app.get("/api/admin/health")
async def admin_health():
    return {"status": "healthy", "mode": "fallback", "admin": True}