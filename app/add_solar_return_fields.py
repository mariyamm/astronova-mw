"""
Database migration to add Solar Return fields

This script adds the new fields needed for Solar Return product type:
- person1_birthday_location: Location where birthday is celebrated
- person1_birthday_latitude: Latitude of birthday location
- person1_birthday_longitude: Longitude of birthday location
"""

import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from db.database import engine


def add_solar_return_fields():
    """Add Solar Return fields to the analyses table"""
    print("🚀 Adding Solar Return fields to database...")
    
    with engine.connect() as conn:
        try:
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'analyses' 
                AND column_name IN ('person1_birthday_location', 'person1_birthday_latitude', 'person1_birthday_longitude')
            """))
            existing_columns = [row[0] for row in result]
            
            if len(existing_columns) == 3:
                print("ℹ️  Solar Return fields already exist in the database")
                return
            
            print(f"📊 Adding new columns to 'analyses' table...")
            
            # Add person1_birthday_location column
            if 'person1_birthday_location' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE analyses 
                    ADD COLUMN person1_birthday_location VARCHAR(300)
                """))
                conn.commit()
                print("✅ Added person1_birthday_location column")
            else:
                print("ℹ️  person1_birthday_location column already exists")
            
            # Add person1_birthday_latitude column
            if 'person1_birthday_latitude' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE analyses 
                    ADD COLUMN person1_birthday_latitude DOUBLE PRECISION
                """))
                conn.commit()
                print("✅ Added person1_birthday_latitude column")
            else:
                print("ℹ️  person1_birthday_latitude column already exists")
            
            # Add person1_birthday_longitude column
            if 'person1_birthday_longitude' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE analyses 
                    ADD COLUMN person1_birthday_longitude DOUBLE PRECISION
                """))
                conn.commit()
                print("✅ Added person1_birthday_longitude column")
            else:
                print("ℹ️  person1_birthday_longitude column already exists")
            
            print("🎉 Migration completed successfully!")
            print("\n" + "="*60)
            print("Solar Return fields have been added to the database.")
            print("You can now process Solar Return orders from Shopify.")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    add_solar_return_fields()
