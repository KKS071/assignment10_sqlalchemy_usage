# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from .config import settings

# Create SQLAlchemy engine
def get_engine(database_url: str = settings.DATABASE_URL):
    try:
        engine = create_engine(database_url, echo=True)  # Echo logs SQL queries
        return engine
    except SQLAlchemyError as e:
        print(f"Failed to create engine: {e}")
        raise

# Create session factory
def get_sessionmaker(engine):
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

# Initialize engine and session
engine = get_engine()
SessionLocal = get_sessionmaker(engine)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()