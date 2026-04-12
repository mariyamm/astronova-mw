from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class PermissionBase(BaseModel):
    """Base permission schema"""
    name: str
    code: str
    description: Optional[str] = None


class PermissionCreate(PermissionBase):
    """Permission creation schema"""
    pass


class PermissionUpdate(BaseModel):
    """Permission update schema"""
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None


class PermissionResponse(PermissionBase):
    """Permission response schema"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
