from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import threading

from app.database import SessionLocal
from app.models import User, Query as QueryModel, AuditLog
from app.api.auth import get_current_user
from app.services.agents.graph import MultiAgentGraph
from app.services.evaluation import RAGEvaluator

router = APIRouter(prefix="/rag", tags=["RAG"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_background_ragas_evaluation(query: str, answer: str, contexts: list):
    """
    This runs in a completely separate thread AFTER the user gets their response.
    """
    print("[BACKGROUND THREAD] Starting deep Ragas evaluation...")
    try:
        evaluator = RAGEvaluator()
        scores = evaluator.evaluate(query=query, answer=answer, contexts=contexts)
        print(f"[BACKGROUND THREAD] Ragas Scores -> Faithfulness: {scores.get('faithfulness')}, Relevancy: {scores.get('answer_relevancy')}")
    except Exception as e:
        print(f"[BACKGROUND THREAD] Ragas evaluation failed: {e}")

@router.post("/query")
def ask_question(
    question: str = Query(..., description="The question to ask the AI"),
    document_id: str = Query(None, description="Optional: Limit search to a specific document ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    agent_graph = MultiAgentGraph()
    compiled_graph = agent_graph.build_graph()

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
        final_state = compiled_graph.invoke(initial_state)
        
        answer = final_state["answer"]
        context_chunks = final_state["context_chunks"]
        retries = final_state["retries"]

    except ValueError as e:
        if str(e) == "PROMPT_INJECTION_DETECTED":
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
        raise e

    # Start the heavy evaluation in a background thread (Non-blocking)
    thread = threading.Thread(
        target=run_background_ragas_evaluation, 
        args=(question, answer, [c.get("text", "") for c in context_chunks])
    )
    thread.start()

    # Log the successful query to PostgreSQL
    new_query = QueryModel(
        user_id=current_user.id,
        document_id=document_id,
        question=question,
        answer=answer
    )
    db.add(new_query)
    db.commit()

    # Return the answer IMMEDIATELY to the user
    return {
        "answer": answer,
        "sources": [chunk.get("text", "") for chunk in context_chunks],
        "pii_redacted_count": 0,
        "blocked": False,
        "agent_retries": retries - 1
    }