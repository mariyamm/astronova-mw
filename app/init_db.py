"""
Database initialization script

This script creates all database tables and seeds initial data:
- Creates all permissions
- Creates a default admin user (username: admin, password: admin123)
"""

import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from db.database import engine, SessionLocal
from db.base import Base
from models.user import User
from models.permission import Permission
from core.security import get_password_hash
from permissions.codes import ALL_PERMISSIONS


def init_db():
    """Initialize the database"""
    print("🚀 Initializing AstroNova database...")
    
    # Create all tables
    print("📊 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Check if permissions already exist
        existing_permissions = db.query(Permission).count()
        
        if existing_permissions == 0:
            print("🔐 Creating permissions...")
            
            # Create all permissions
            for perm_data in ALL_PERMISSIONS:
                permission = Permission(
                    name=perm_data["name"],
                    code=perm_data["code"],
                    description=perm_data["description"]
                )
                db.add(permission)
            
            db.commit()
            print(f"✅ Created {len(ALL_PERMISSIONS)} permissions")
        else:
            print(f"ℹ️  Permissions already exist ({existing_permissions} found)")
        
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            print("👤 Creating default admin user...")
            
            # Get all permissions
            all_permissions = db.query(Permission).all()
            
            # Create admin user
            admin_user = User(
                username="admin",
                first_name="Администратор",
                last_name="Системен",
                hashed_password=get_password_hash("Admin@123"),
                role="admin",
                is_active=True
            )
            
            # Assign all permissions to admin
            admin_user.permissions = all_permissions
            
            db.add(admin_user)
            db.commit()
            
            print("✅ Admin user created successfully")
            print("\n" + "="*50)
            print("📋 Default Admin Credentials:")
            print("   Username: admin")
            print("   Password: Admin@123")
            print("="*50)
            print("⚠️  ВАЖНО: Сменете паролата след първия вход!")
            print("="*50 + "\n")
        else:
            print("ℹ️  Admin user already exists")
        
        print("🎉 Database initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
