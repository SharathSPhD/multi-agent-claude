"""
Database configuration and session management.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# Database URL from environment or default to SQLite in project root
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///../mcp_multiagent.db"
)

# For PostgreSQL in production:
# DATABASE_URL = "postgresql://user:password@localhost/mcp_multiagent"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    # SQLite specific settings
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"  # Enable SQL logging if needed
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import Base from models to ensure consistency
# Base = declarative_base()  # Removed - use models.Base instead


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that provides database session.
    Used with FastAPI's Depends() for automatic session management.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database by creating all tables.
    Called during application startup.
    """
    from models import Base
    Base.metadata.create_all(bind=engine)


def reset_db():
    """
    Reset database by dropping and recreating all tables.
    WARNING: This will delete all data!
    """
    from models import Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)