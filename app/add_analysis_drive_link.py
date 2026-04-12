"""
Migration: Add drive_link column to analyses table and backfill from pdf_jobs.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from db.database import engine

def migrate():
    with engine.connect() as conn:
        # Add drive_link column to analyses
        conn.execute(text("""
            ALTER TABLE analyses
            ADD COLUMN IF NOT EXISTS drive_link VARCHAR(500)
        """))
        conn.commit()
        print("Added drive_link column to analyses table.")

        # Backfill: copy latest drive_link from pdf_jobs into analyses
        result = conn.execute(text("""
            UPDATE analyses a
            SET drive_link = sub.drive_link
            FROM (
                SELECT DISTINCT ON (analysis_id) analysis_id, drive_link
                FROM pdf_jobs
                WHERE drive_link IS NOT NULL
                ORDER BY analysis_id, created_at DESC
            ) sub
            WHERE a.id = sub.analysis_id AND a.drive_link IS NULL
        """))
        conn.commit()
        print(f"Backfilled {result.rowcount} analyses with drive_link from pdf_jobs.")

if __name__ == "__main__":
    migrate()
