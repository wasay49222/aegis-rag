from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Connection string matching our docker-compose.yml
SQLALCHEMY_DATABASE_URL = "postgresql://aegis_user:aegis_password@localhost:5432/aegis_db"

# Create the engine (the connection to the database)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a session factory (used to interact with the database)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our database models
Base = declarative_base()