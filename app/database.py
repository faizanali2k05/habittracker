from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool, StaticPool
import os
from typing import Generator

import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
# Load environment variables from .env file, overriding existing system variables
load_dotenv(override=True)

# Get database URL from environment variable or Streamlit secrets
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    try:
        # Try fetching from Streamlit secrets
        if "DATABASE_URL" in st.secrets:
            DATABASE_URL = st.secrets["DATABASE_URL"]
    except (FileNotFoundError, AttributeError):
        pass

# Fallback to SQLite if no URL found
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./habit_tracker.db"

# Fix Supabase/Heroku postgres:// schema for SQLAlchemy
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure engine based on database type
if "sqlite" in DATABASE_URL:
    # SQLite configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
else:
    # PostgreSQL configuration with connection pooling
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create declarative base for models
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency function to get database session.
    Yields the session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables.
    Creates all tables defined in models.
    """
    Base.metadata.create_all(bind=engine)
