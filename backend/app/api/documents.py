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

# Create the router
router = APIRouter(prefix="/documents", tags=["Documents"])

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
    current_user: User = Depends(get_current_user) # Requires login!
):
    """
    Accepts a file, parses it, chunks it, and saves it to the database.
    """
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

    # 5. Save Document record to PostgreSQL
    new_doc = Document(
        user_id=current_user.id,
        title=file.filename,
        file_path=file_path,
        chunk_count=len(chunks)
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # 6. Save Chunks records to PostgreSQL
    for index, chunk_text in enumerate(chunks):
        new_chunk = Chunk(
            document_id=new_doc.id,
            chunk_index=index,
            text=chunk_text
        )
        db.add(new_chunk)
    
    db.commit()

    # 7. Return the result
    return {
        "message": "Document uploaded and processed successfully",
        "document_id": str(new_doc.id),
        "chunk_count": len(chunks)
    }