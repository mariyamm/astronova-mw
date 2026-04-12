"""
Update admin user password

This script updates the admin user's password to Admin@123
"""

import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from db.database import SessionLocal
from models.user import User
from models.permission import Permission  # Import Permission model
from core.security import get_password_hash


def update_admin_password():
    """Update the admin user's password"""
    print("🔐 Updating admin password...")
    
    db = SessionLocal()
    
    try:
        # Find the admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            print("❌ Admin user not found!")
            return False
        
        # Update the password
        admin_user.hashed_password = get_password_hash("Admin@123")
        db.commit()
        
        print("✅ Admin password updated successfully!")
        print("\n" + "="*50)
        print("📋 Admin Credentials:")
        print("   Username: admin")
        print("   Password: Admin@123")
        print("="*50 + "\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating password: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    update_admin_password()
