"""
Update ProductType enum in the database to include SOLAR_RETURN

This script adds the new SOLAR_RETURN value to the existing producttype enum
"""

import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from db.database import engine


def update_product_type_enum():
    """Add SOLAR_RETURN to the producttype enum"""
    print("🚀 Updating ProductType enum in database...")
    
    with engine.connect() as conn:
        try:
            # Check if SOLAR_RETURN already exists in the enum
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM pg_type t 
                    JOIN pg_enum e ON t.oid = e.enumtypid  
                    WHERE t.typname = 'producttype' 
                    AND e.enumlabel = 'solar_return'
                )
            """))
            
            exists = result.scalar()
            
            if exists:
                print("ℹ️  'solar_return' value already exists in producttype enum")
                return
            
            print("📊 Adding 'solar_return' to producttype enum...")
            
            # Add new enum value
            # Note: ALTER TYPE ... ADD VALUE cannot run inside a transaction block
            conn.execute(text("COMMIT"))
            conn.execute(text("""
                ALTER TYPE producttype ADD VALUE 'solar_return'
            """))
            
            print("✅ Successfully added 'solar_return' to producttype enum")
            print("\n" + "="*60)
            print("ProductType enum has been updated.")
            print("The system can now process Solar Return orders.")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"❌ Error during enum update: {e}")
            raise


if __name__ == "__main__":
    update_product_type_enum()
