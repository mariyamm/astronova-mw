from sqlalchemy import Column, Integer, String, Boolean, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base


# Association table for many-to-many relationship between users and permissions
user_permissions = Table(
    'user_permissions',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
)


class User(Base):
    """User model with authentication and permissions"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # admin, editor, user
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    permissions = relationship(
        "Permission",
        secondary=user_permissions,
        back_populates="users",
        lazy="joined"
    )
    
    def __repr__(self):
        return f"<User {self.username}>"
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission"""
        return any(p.name == permission_name for p in self.permissions)
    
    def is_admin(self) -> bool:
        """Check if user is an admin"""
        return self.role == "admin"
