from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from models.user import User
from models.permission import Permission
from schemas.permission import PermissionResponse
from auth.dependencies import get_current_admin


router = APIRouter(prefix="/api/permissions", tags=["Permissions"])


@router.get("/", response_model=List[PermissionResponse])
async def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    List all available permissions (Admin only)
    """
    permissions = db.query(Permission).all()
    return permissions
