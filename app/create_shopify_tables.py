"""
Create Shopify tables

This script creates the Shopify order and analysis tables in the database
"""

import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from db.database import engine
from db.base import Base


def create_shopify_tables():
    """Create Shopify-related tables"""
    print("🔧 Creating Shopify tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Shopify tables created successfully!")
        print("   - shopify_orders")
        print("   - analyses")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    return True


if __name__ == "__main__":
    create_shopify_tables()
