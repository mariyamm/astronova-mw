import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi import Request
import json, httpx

# Import API routers
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.permissions import router as permissions_router
from app.api.admin import router as admin_router
from app.api.shopify import router as shopify_router

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

# Include API routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(permissions_router)
app.include_router(admin_router)
app.include_router(shopify_router)


@app.get("/")
async def root():
    """Root endpoint - redirect to admin interface"""
    return RedirectResponse(url="/login.html")


@app.get("/admin/dashboard.html")
async def admin_dashboard():
    """Redirect admin dashboard to dashboard.html"""
    return RedirectResponse(url="/dashboard.html")


@app.get("/admin/{path:path}")
async def admin_redirect(path: str):
    """Redirect admin paths to root level"""
    return RedirectResponse(url=f"/{path}")


# ── Google Drive one-time OAuth ──────────────────────────────────────────────
_GDRIVE_CLIENT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drive_oauth_client.json")
_GDRIVE_TOKEN_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gdrive_token.json")
_GDRIVE_SCOPES      = ["https://www.googleapis.com/auth/drive.file"]
_GDRIVE_REDIRECT    = "http://localhost:8000/gdrive-callback"


@app.get("/gdrive-authorize")
async def gdrive_authorize():
    """Start Google Drive OAuth flow — opens Google sign-in."""
    with open(_GDRIVE_CLIENT_PATH) as f:
        cred = json.load(f).get("web") or json.load(open(_GDRIVE_CLIENT_PATH)).get("installed")
    with open(_GDRIVE_CLIENT_PATH) as f:
        raw = json.load(f)
    cred = raw.get("web") or raw.get("installed")
    auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={cred['client_id']}"
        f"&redirect_uri={_GDRIVE_REDIRECT}"
        f"&response_type=code"
        f"&scope={'%20'.join(_GDRIVE_SCOPES)}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    return RedirectResponse(auth_url)


@app.get("/gdrive-callback")
async def gdrive_callback(request: Request):
    """Handle OAuth callback — exchange code for token and save."""
    code = request.query_params.get("code")
    error = request.query_params.get("error")
    if error:
        return HTMLResponse(f"<h2>Authorization failed</h2><p>{error}</p>", status_code=400)
    if not code:
        return HTMLResponse("<h2>No code received</h2>", status_code=400)

    with open(_GDRIVE_CLIENT_PATH) as f:
        raw = json.load(f)
    cred = raw.get("web") or raw.get("installed")

    async with httpx.AsyncClient() as client:
        resp = await client.post(cred.get("token_uri", "https://oauth2.googleapis.com/token"), data={
            "code": code,
            "client_id": cred["client_id"],
            "client_secret": cred["client_secret"],
            "redirect_uri": _GDRIVE_REDIRECT,
            "grant_type": "authorization_code",
        })

    if resp.status_code != 200:
        return HTMLResponse(f"<h2>Token exchange failed</h2><pre>{resp.text}</pre>", status_code=500)

    token_data = resp.json()
    token_file = {
        "token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token"),
        "token_uri": cred.get("token_uri", "https://oauth2.googleapis.com/token"),
        "client_id": cred["client_id"],
        "client_secret": cred["client_secret"],
        "scopes": _GDRIVE_SCOPES,
    }

    with open(_GDRIVE_TOKEN_PATH, "w") as f:
        json.dump(token_file, f, indent=2)

    return HTMLResponse(
        "<h2 style='color:green'>✅ Google Drive authorized successfully!</h2>"
        "<p>Token saved. PDFs will now be uploaded to Google Drive automatically.</p>"
        "<p>You can close this tab.</p>"
    )
# ─────────────────────────────────────────────────────────────────────────────
    

# Mount static files AFTER defining routes to avoid conflicts
# This serves all files in the static directory at the root level
import os
static_dir = "static" if os.path.exists("static") else "app/static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "message": "AstroNova Admin API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth/login",
            "users": "/api/users/",
            "permissions": "/api/permissions/",
            "admin": "/api/admin/stats"
        }
    }
