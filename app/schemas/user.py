from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.permission import PermissionResponse


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(default="user", pattern="^(admin|editor|user)$")


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=6)
    permission_ids: Optional[List[int]] = []


class UserUpdate(BaseModel):
    """User update schema"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[str] = Field(None, pattern="^(admin|editor|user)$")
    is_active: Optional[bool] = None
    permission_ids: Optional[List[int]] = None


class UserResponse(UserBase):
    """User response schema"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    permissions: List[PermissionResponse] = []
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """User login schema"""
    username: str
    password: str
