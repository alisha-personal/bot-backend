# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import os
from .config import load_config

# Use environment variables for database connection
DATABASE_URL = load_config()

engine = create_engine(
    DATABASE_URL, 
    poolclass=NullPool  # Disable connection pooling for better connection management
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Database session generator for dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()