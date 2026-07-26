# backend/app/api/rag.py
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import User, AuditLog, Query as QueryModel, Document
from app.api.auth import get_current_user

# Import your actual services
from app.services.agents.graph import compiled_graph
from app.services.pii_guardrail import PIIGuardrail
from app.services.injection_guardrail import InjectionGuardrail

router = APIRouter(prefix="/rag", tags=["RAG"])

class QueryRequest(BaseModel):
    question: str
    document_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    pii_redacted_count: int = 0
    blocked: bool = False
    agent_retries: int = 0

def log_audit_event(db: Session, event_type: str, user_id: str, details: Dict[str, Any]):
    """Helper function to log audit events"""
    try:
        audit_entry = AuditLog(
            id=str(uuid.uuid4()),
            event_type=event_type,
            user_id=user_id,
            details=details,
            created_at=datetime.now(timezone.utc)
        )
        db.add(audit_entry)
        db.commit()
    except Exception as e:
        print(f"Failed to write audit log: {e}")
        db.rollback()

@router.post("/query", response_model=QueryResponse)
async def ask_question(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = str(current_user.id)
    
    # Initialize guardrails
    pii_guardrail = PIIGuardrail()
    injection_guardrail = InjectionGuardrail()
    
    try:
        # Step 1: Check for prompt injection
        is_safe = injection_guardrail.is_safe(request.question)
        if not is_safe:
            log_audit_event(
                db=db,
                event_type="INJECTION_BLOCKED",
                user_id=user_id,
                details={"question": request.question, "reason": "Blocked by DeBERTa Classifier"}
            )
            raise HTTPException(status_code=403, detail="Query blocked: Potential prompt injection detected")
        
        # Step 2: Redact PII
        redacted_text, pii_entities = pii_guardrail.redact(request.question)
        if pii_entities:
            log_audit_event(
                db=db,
                event_type="PII_REDACTED",
                user_id=user_id,
                details={
                    "original_question": request.question,
                    "redacted_question": redacted_text,
                    "entities": pii_entities,
                    "count": len(pii_entities)
                }
            )
        
        # Step 3: Prepare initial state for LangGraph (MATCHES AgentState EXACTLY)
        initial_state = {
            "query": redacted_text,
            "user_id": user_id,
            "document_id": request.document_id or "",
            "context_chunks": [],
            "answer": "",
            "critique": "",
            "retries": 0
        }
        
        # Step 4: Invoke the Multi-Agent Graph
        final_state = compiled_graph.invoke(initial_state)
        
        answer = final_state.get("answer", "I cannot confidently answer based on the provided documents.")
        
        # Extract sources from context chunks
        sources = [chunk.get("text", "") for chunk in final_state.get("context_chunks", [])]
        agent_retries = final_state.get("retries", 0)
        
        # Step 5: Log the successful query to the queries table
        query_record = QueryModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            document_id=request.document_id,
            question=request.question,
            answer=answer,
            created_at=datetime.now(timezone.utc)
        )
        db.add(query_record)
        
        # Step 6: Log the query execution to audit logs
        log_audit_event(
            db=db,
            event_type="QUERY_EXECUTED",
            user_id=user_id,
            details={
                "question": request.question,
                "answer_length": len(answer),
                "sources_count": len(sources),
                "agent_retries": agent_retries
            }
        )
        
        db.commit()
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            pii_redacted_count=len(pii_entities),
            blocked=False,
            agent_retries=agent_retries
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        log_audit_event(
            db=db,
            event_type="QUERY_FAILED",
            user_id=user_id,
            details={"question": request.question, "error": str(e), "error_type": type(e).__name__}
        )
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")