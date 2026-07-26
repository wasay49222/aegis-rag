# backend/app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# FORCE the correct credentials that match your docker-compose.yml
# This bypasses any .env loading issues.
DATABASE_URL = "postgresql://aegis_user:aegis_password@localhost:5432/aegis_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()