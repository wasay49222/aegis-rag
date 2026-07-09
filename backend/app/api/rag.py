from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User, Query as QueryModel
from app.api.auth import get_current_user
from app.services.rag import RAGPipeline

# Create the router
router = APIRouter(prefix="/rag", tags=["RAG"])

# Helper to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/query")
def ask_question(
    question: str = Query(..., description="The question to ask the AI"),
    document_id: str = Query(None, description="Optional: Limit search to a specific document ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Initialize the pipeline
    pipeline = RAGPipeline()

    # 2. Retrieve relevant chunks (Now returns chunks AND an audit log)
    context_chunks, retrieval_pii_log = pipeline.retrieve(
        query=question,
        user_id=str(current_user.id),
        document_id=document_id,
        top_k=3 
    )

    if not context_chunks:
        return {"answer": "I don't know. No relevant context was found.", "sources": [], "pii_redacted": []}

    # 3. Generate the answer (Now returns answer AND an audit log)
    answer, generation_pii_log = pipeline.generate_answer(question, context_chunks)

    # 4. Combine all PII logs for the database
    all_pii_logs = retrieval_pii_log + generation_pii_log

    # 5. Log to PostgreSQL (Audit Trail)
    new_query = QueryModel(
        user_id=current_user.id,
        document_id=document_id,
        question=question, # Log the ORIGINAL question for the audit
        answer=answer      # Log the SANITIZED answer
    )
    db.add(new_query)
    db.commit()

    # 6. Return the sanitized answer and sources
    return {
        "answer": answer,
        "sources": [chunk.get("text", "") for chunk in context_chunks],
        "pii_redacted_count": len(all_pii_logs) # Show the frontend how much PII was blocked
    }