"""
Database migration to add solar_return_year field

This script adds the solar_return_year field to the analyses table
for tracking which year a solar return analysis is for (e.g., 2025, 2026).
"""

from sqlalchemy import create_engine, text, Integer
from db.database import SQLALCHEMY_DATABASE_URL
import sys


def add_solar_return_year_field():
    """Add solar_return_year field to the analyses table"""
    print("🚀 Adding solar_return_year field to database...")
    
    # Create engine
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='analyses' 
                AND column_name='solar_return_year'
            """))
            
            if result.fetchone():
                print("ℹ️  solar_return_year field already exists in the database")
                return True
            
            # Add the new column
            print("📊 Adding solar_return_year column to analyses table...")
            conn.execute(text("""
                ALTER TABLE analyses 
                ADD COLUMN solar_return_year INTEGER
            """))
            conn.commit()
            
            print("✅ Successfully added solar_return_year field!")
            print("\nColumn added:")
            print("  - solar_return_year (INTEGER) - The year for the solar return analysis")
            print("\nYou can now:")
            print("  1. Process new Solar Return orders with year information")
            print("  2. Edit existing analyses to add the year")
            print("  3. View the year in the Shopify orders interface")
            
            return True
            
    except Exception as e:
        print(f"❌ Error adding solar_return_year field: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        engine.dispose()


if __name__ == "__main__":
    success = add_solar_return_year_field()
    sys.exit(0 if success else 1)
