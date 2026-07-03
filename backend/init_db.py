from sqlalchemy import text
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.database import engine, Base
from app.models import User, Document, Chunk, Query, AuditLog

def init_postgres():
    print("1. Creating PostgreSQL tables...")
    Base.metadata.create_all(bind=engine)
    print("   -> Tables created.")

    print("2. Enabling Row-Level Security (RLS)...")
    with engine.connect() as conn:
        # Enable RLS on all tables
        tables = ["users", "documents", "chunks", "queries", "audit_logs"]
        for table in tables:
            conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
        
        conn.commit()
    print("   -> RLS enabled. (Policies will be linked to JWTs in Level 3).")

def init_qdrant():
    print("3. Initializing Qdrant...")
    # Connect to the local Qdrant instance
    client = QdrantClient(host="localhost", port=6333)
    
    # Check if collection already exists to prevent errors
    collections = [c.name for c in client.get_collections().collections]
    
    if "aegis_chunks" not in collections:
        print("   -> Creating 'aegis_chunks' collection...")
        client.create_collection(
            collection_name="aegis_chunks",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print("   -> Collection created (Size: 384, Distance: Cosine).")
    else:
        print("   -> Collection 'aegis_chunks' already exists. Skipping.")

if __name__ == "__main__":
    print("Starting Aegis-RAG Database Initialization...\n")
    init_postgres()
    init_qdrant()
    print("\nInitialization complete!")