from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User, Query as QueryModel, AuditLog
from app.api.auth import get_current_user
from app.services.agents.graph import MultiAgentGraph

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
    # 1. Initialize the Multi-Agent Graph
    agent_graph = MultiAgentGraph()
    compiled_graph = agent_graph.build_graph()

    # 2. Define the initial state (the shared whiteboard for the agents)
    initial_state = {
        "query": question,
        "user_id": str(current_user.id),
        "document_id": document_id,
        "context_chunks": [],
        "answer": "",
        "critique": "",
        "retries": 0
    }

    try:
        # 3. RUN THE GRAPH! 
        # This triggers the Researcher, then the Critic, and loops if rejected.
        final_state = compiled_graph.invoke(initial_state)
        
        # Extract the final results from the whiteboard
        answer = final_state["answer"]
        context_chunks = final_state["context_chunks"]
        retries = final_state["retries"]

    except ValueError as e:
        if str(e) == "PROMPT_INJECTION_DETECTED":
            # Log the attack to the Audit Database
            new_audit = AuditLog(
                event_type="PROMPT_INJECTION_BLOCKED",
                user_id=current_user.id,
                details={"malicious_query": question}
            )
            db.add(new_audit)
            db.commit()

            return {
                "answer": "Error: Your request was blocked by the security guardrails due to suspicious content.",
                "sources": [],
                "pii_redacted_count": 0,
                "blocked": True,
                "agent_retries": 0
            }
        # If it's a different error, let it crash so we can debug
        raise e

    # 4. Log the successful query to PostgreSQL
    new_query = QueryModel(
        user_id=current_user.id,
        document_id=document_id,
        question=question,
        answer=answer
    )
    db.add(new_query)
    db.commit()

    # 5. Return the final answer and the debate stats
    return {
        "answer": answer,
        "sources": [chunk.get("text", "") for chunk in context_chunks],
        "pii_redacted_count": 0,
        "blocked": False,
        "agent_retries": retries - 1 # Shows how many times the Critic rejected the answer
    }