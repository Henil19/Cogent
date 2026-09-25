"""
Cogent Database Module
SQLAlchemy engine, session management, and Base class.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings


# Graceful database engine initialization
db_url = settings.DATABASE_URL
engine_kwargs = {
    "echo": (settings.ENVIRONMENT == "development"),
}

import warnings
from sqlalchemy import text
from sqlalchemy.pool import StaticPool

try:
    if "postgresql" in db_url:
        import psycopg  # Verify psycopg driver presence
        # Test connection with a short 2-second timeout
        test_engine = create_engine(
            db_url,
            connect_args={"connect_timeout": 2},
            **engine_kwargs
        )
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            **engine_kwargs
        )
    else:
        engine = create_engine(db_url, **engine_kwargs)
except Exception as e:
    warnings.warn(f"PostgreSQL unreachable ({str(e)}). Falling back to SQLite local database.")
    # Local persistent SQLite database in backend/data/cogent.db
    data_dir = settings.BASE_DIR / "data" if hasattr(settings, "BASE_DIR") else Path(__file__).resolve().parent.parent / "data"
    os.makedirs(data_dir, exist_ok=True)
    sqlite_path = data_dir / "cogent_app.db"
    db_url = f"sqlite:///{sqlite_path}"
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        **engine_kwargs
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_db():
    """
    Dependency injection for database sessions.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
