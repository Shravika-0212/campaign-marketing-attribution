"""Database connection, session management, and SQLite configuration."""
import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from backend.app.models.base import Base
# Import all entities to ensure they are registered with Base.metadata
from backend.app.models.entities import (
    Channel, Audience, Creative, Campaign, Contact, WebSession,
    Touchpoint, Lead, Opportunity, Order, CostRecord, AttributionResult,
    CampaignChannel, CampaignAudience, CampaignCreative, ContactIdentity,
    EventHistory, AnomalyIssue, AttributionModel, DataGenerationRun,
    ValidationResult
)

# Database path resolution
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "marketing_attribution.sqlite3"
DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

# Create SQLAlchemy engine
engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# Enforce foreign key constraints and enable WAL mode in SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI dependency for yielding database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all database tables."""
    # Ensure parent directory exists
    db_file_path = Path(engine.url.database) if engine.url.database else None
    if db_file_path and not db_file_path.is_absolute():
        db_file_path = Path.cwd() / db_file_path
    if db_file_path and db_file_path.parent:
        db_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")

def reset_db():
    """Drop and recreate all database tables."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database tables reset successfully.")
