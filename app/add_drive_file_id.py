"""
Migration: add drive_file_id column to pdf_jobs table.
Run once: python add_drive_file_id.py
"""
import os
import sys

sys.path.insert(0, "/app")

import psycopg2

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/astronova",
)

# Parse the URL to get individual connection params
import re
match = re.match(
    r"postgresql://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:/]+)(?::(?P<port>\d+))?/(?P<dbname>.+)",
    DATABASE_URL,
)
if not match:
    raise ValueError(f"Could not parse DATABASE_URL: {DATABASE_URL}")

conn = psycopg2.connect(
    host=match.group("host"),
    port=int(match.group("port") or 5432),
    user=match.group("user"),
    password=match.group("password"),
    dbname=match.group("dbname"),
)

with conn:
    with conn.cursor() as cur:
        cur.execute("""
            ALTER TABLE pdf_jobs
            ADD COLUMN IF NOT EXISTS drive_file_id VARCHAR(200);
        """)
        cur.execute("""
            ALTER TABLE pdf_jobs
            ADD COLUMN IF NOT EXISTS drive_link VARCHAR(500);
        """)
        print("drive_file_id and drive_link columns added (or already exist).")

conn.close()
