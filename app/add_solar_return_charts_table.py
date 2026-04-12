"""
Migration: Add solar_return_charts table

Run this script to create the solar_return_charts table in an existing database.
Usage: python add_solar_return_charts_table.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from db.database import engine


def add_solar_return_charts_table():
    print("🔧 Adding solar_return_charts table...")

    with engine.connect() as conn:
        # Check if table already exists
        result = conn.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables "
            "WHERE table_name = 'solar_return_charts')"
        ))
        exists = result.scalar()

        if exists:
            print("✅ Table 'solar_return_charts' already exists — nothing to do.")
            return

        conn.execute(text("""
            CREATE TABLE solar_return_charts (
                id          SERIAL PRIMARY KEY,
                analysis_id INTEGER NOT NULL UNIQUE REFERENCES analyses(id) ON DELETE CASCADE,
                chart_data  TEXT NOT NULL,
                generated_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at   TIMESTAMPTZ
            )
        """))
        conn.execute(text(
            "CREATE INDEX ix_solar_return_charts_analysis_id ON solar_return_charts (analysis_id)"
        ))
        conn.commit()

    print("✅ Table 'solar_return_charts' created successfully.")


if __name__ == "__main__":
    add_solar_return_charts_table()
