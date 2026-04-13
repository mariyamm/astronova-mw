from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime

from app.db.database import get_db
from app.models.user import User
from app.models.permission import Permission
from app.auth.dependencies import get_current_admin


router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for monitoring and load balancers
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "AstroNova API",
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "AstroNova API",
            "version": "1.0.0",
            "database": "disconnected",
            "error": str(e)
        }


@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get dashboard statistics (Admin only)
    """
    # Count users by role
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    admin_count = db.query(func.count(User.id)).filter(User.role == "admin").scalar()
    editor_count = db.query(func.count(User.id)).filter(User.role == "editor").scalar()
    user_count = db.query(func.count(User.id)).filter(User.role == "user").scalar()
    total_permissions = db.query(func.count(Permission.id)).scalar()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "admin_count": admin_count,
        "editor_count": editor_count,
        "user_count": user_count,
        "total_permissions": total_permissions
    }
