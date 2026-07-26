# backend/app/api/audit.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional

from app.database import get_db
from app.models import AuditLog

router = APIRouter(prefix="/audit", tags=["Audit Logs"])

@router.get("/logs")
def get_audit_logs(
    limit: int = 50,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Fetch audit logs from the database."""
    query = db.query(AuditLog)
    
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    
    # Get most recent logs first
    logs = query.order_by(desc(AuditLog.created_at)).limit(limit).all()
    
    return [
        {
            "id": str(log.id),
            "event_type": log.event_type,
            "user_id": str(log.user_id) if log.user_id else "system",
            "details": log.details,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        for log in logs
    ]

@router.get("/stats")
def get_audit_stats(db: Session = Depends(get_db)):
    """Get summary statistics for the audit dashboard."""
    pii_count = db.query(AuditLog).filter(AuditLog.event_type == "PII_REDACTED").count()
    injection_count = db.query(AuditLog).filter(AuditLog.event_type == "INJECTION_BLOCKED").count()
    hallucination_count = db.query(AuditLog).filter(AuditLog.event_type == "HALLUCINATION_FLAGGED").count()
    document_count = db.query(AuditLog).filter(AuditLog.event_type == "DOCUMENT_INGESTED").count()
    
    return {
        "pii_redactions": pii_count,
        "injections_blocked": injection_count,
        "hallucinations": hallucination_count,
        "documents": document_count
    }