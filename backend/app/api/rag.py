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
    """
    Takes a question, retrieves context from Qdrant, generates an answer via Llama 3,
    and logs the interaction for compliance.
    """
    # 1. Initialize the pipeline (The Brain)
    pipeline = RAGPipeline()

    # 2. Retrieve relevant chunks
    context_chunks = pipeline.retrieve(
        query=question,
        user_id=str(current_user.id),
        document_id=document_id,
        top_k=3 # We only need the top 3 most relevant chunks
    )

    # If no context is found, return immediately
    if not context_chunks:
        return {"answer": "I don't know. No relevant context was found.", "sources": []}

    # 3. Generate the answer using Llama 3
    answer = pipeline.generate_answer(question, context_chunks)

    # 4. Log to PostgreSQL (Audit Trail for Compliance)
    # Note: We use 'QueryModel' because 'Query' is already used by FastAPI above
    new_query = QueryModel(
        user_id=current_user.id,
        document_id=document_id,
        question=question,
        answer=answer
    )
    db.add(new_query)
    db.commit()

    # 5. Return the answer and the source text used to generate it
    return {
        "answer": answer,
        "sources": [chunk.get("text", "") for chunk in context_chunks]
    }