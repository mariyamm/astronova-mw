from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings
import os

# Create base class for models first
Base = declarative_base()

# Initialize engine and session as None
engine = None
SessionLocal = None

def init_database():
    """Initialize database connection - call this after environment is ready"""
    global engine, SessionLocal
    try:
        database_url = getattr(settings, 'DATABASE_URL', os.getenv('DATABASE_URL', 'sqlite:///./test.db'))
        engine = create_engine(database_url, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return True
    except Exception as e:
        print(f"Database initialization failed: {e}")
        return False

# Try to initialize database, but don't fail if it's not available
try:
    init_database()
except Exception as e:
    print(f"Warning: Database not available at startup: {e}")


def get_db():
    """Dependency to get database session"""
    if SessionLocal is None:
        if not init_database():
            raise Exception("Database not available")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
