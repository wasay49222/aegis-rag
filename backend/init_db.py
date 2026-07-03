from app.database import engine, Base
from app.models import User, Document, Chunk, Query, AuditLog

def init_database():
    print("Connecting to PostgreSQL and creating tables...")
    # This command creates all tables defined in the models
    Base.metadata.create_all(bind=engine)
    print("Successfully created all tables!")

if __name__ == "__main__":
    init_database()