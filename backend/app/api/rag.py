from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User, Query as QueryModel, AuditLog
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
    pipeline = RAGPipeline()

    try:
        # Attempt to retrieve chunks (This will trigger the Injection Guardrail)
        context_chunks, retrieval_pii_log = pipeline.retrieve(
            query=question,
            user_id=str(current_user.id),
            document_id=document_id,
            top_k=3 
        )
    except ValueError as e:
        if str(e) == "PROMPT_INJECTION_DETECTED":
            # 1. LOG THE ATTACK to the Audit Database (SOC2 Compliance)
            new_audit = AuditLog(
                event_type="PROMPT_INJECTION_BLOCKED",
                user_id=current_user.id,
                details={"malicious_query": question}
            )
            db.add(new_audit)
            db.commit()

            # 2. Return a safe, generic refusal to the user
            return {
                "answer": "Error: Your request was blocked by the security guardrails due to suspicious content.",
                "sources": [],
                "pii_redacted_count": 0,
                "blocked": True
            }
        # If it's a different ValueError, let it crash normally so we can debug
        raise e

    if not context_chunks:
        return {"answer": "I don't know. No relevant context was found.", "sources": [], "pii_redacted_count": 0}

    # Generate the answer
    answer, generation_pii_log = pipeline.generate_answer(question, context_chunks)
    all_pii_logs = retrieval_pii_log + generation_pii_log

    # Log the successful query
    new_query = QueryModel(
        user_id=current_user.id,
        document_id=document_id,
        question=question,
        answer=answer
    )
    db.add(new_query)
    db.commit()

    return {
        "answer": answer,
        "sources": [chunk.get("text", "") for chunk in context_chunks],
        "pii_redacted_count": len(all_pii_logs),
        "blocked": False
    }