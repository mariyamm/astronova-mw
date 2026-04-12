"""
Add Shopify permissions to database

This script adds the new Shopify permissions to the database
"""

import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from db.database import SessionLocal
from models.permission import Permission
from permissions.codes import ALL_PERMISSIONS


def add_shopify_permissions():
    """Add Shopify permissions to database"""
    print("📦 Adding Shopify permissions...")
    
    db = SessionLocal()
    
    try:
        # Get all existing permission codes
        existing_permissions = db.query(Permission).all()
        existing_codes = {p.code for p in existing_permissions}
        
        # Find new permissions
        new_permissions_added = 0
        
        for perm_data in ALL_PERMISSIONS:
            if perm_data["code"] not in existing_codes:
                permission = Permission(
                    name=perm_data["name"],
                    code=perm_data["code"],
                    description=perm_data["description"]
                )
                db.add(permission)
                new_permissions_added += 1
                print(f"  ✅ Added: {perm_data['name']}")
        
        if new_permissions_added > 0:
            db.commit()
            print(f"\n✅ Added {new_permissions_added} new permissions")
        else:
            print("ℹ️  No new permissions to add")
        
    except Exception as e:
        print(f"❌ Error adding permissions: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True


if __name__ == "__main__":
    add_shopify_permissions()
