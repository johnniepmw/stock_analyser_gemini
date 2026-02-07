"""
Database configuration and session management.
"""

from sqlmodel import SQLModel, Session, create_engine
from pathlib import Path

# Database file location
DB_PATH = Path(__file__).parent.parent / "stock_analyser.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine
engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables():
    """Create all tables in the database."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get a database session."""
    with Session(engine) as session:
        yield session


def get_direct_session() -> Session:
    """Get a database session directly (not a generator)."""
    return Session(engine)
