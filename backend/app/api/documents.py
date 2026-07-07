import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User, Document, Chunk
from app.api.auth import get_current_user
from app.services.document_parser import extract_text
from app.services.chunker import chunk_recursive
from app.services.embedder import Embedder
from app.services.vector_store import VectorStore

# Create the router
router = APIRouter(prefix="/documents", tags=["Documents"])

# Initialize AI Services globally so they only load once on server startup
embedder = Embedder()
vector_store = VectorStore()
vector_store.initialize_collection()

# Helper to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Ensure the uploads directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
def upload_document(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Validate file type
    if file.content_type not in ["application/pdf", "text/plain"]:
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are allowed.")

    # 2. Save the file locally
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    saved_filename = f"{file_id}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Parse the document
    text = extract_text(file_path)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Document is empty or text could not be extracted.")

    # 4. Chunk the text
    chunks = chunk_recursive(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="Document could not be chunked.")

    # 5. Generate Embeddings (The AI Math)
    embeddings = embedder.embed_texts(chunks)

    # 6. Save Document record to PostgreSQL
    new_doc = Document(
        user_id=current_user.id,
        title=file.filename,
        file_path=file_path,
        chunk_count=len(chunks)
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # 7. Save Chunks to PostgreSQL AND prepare for Qdrant
    chunks_data = []
    for index, chunk_text in enumerate(chunks):
        # Save to PostgreSQL
        new_chunk = Chunk(
            document_id=new_doc.id,
            chunk_index=index,
            text=chunk_text
        )
        db.add(new_chunk)
        
        # Prepare payload for Qdrant (CRITICAL: Must include user_id for security filtering)
        chunks_data.append({
            "document_id": str(new_doc.id),
            "user_id": str(current_user.id),
            "chunk_index": index,
            "text": chunk_text
        })
    
    db.commit()

    # 8. Insert Vectors into Qdrant
    vector_store.insert_chunks(chunks_data, embeddings)

    # 9. Return the result
    return {
        "message": "Document uploaded, chunked, and vectorized successfully",
        "document_id": str(new_doc.id),
        "chunk_count": len(chunks)
    }