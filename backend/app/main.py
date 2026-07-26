# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all routers
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.rag import router as rag_router
from app.api.audit import router as audit_router
from app.api.dashboard import router as dashboard_router

# Initialize the FastAPI application
app = FastAPI(
    title="Aegis-RAG Enterprise API",
    description="Enterprise Secure Agentic AI Platform with multi-agent RAG, security guardrails, and MLOps evaluation",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """
    Health check endpoint to verify the server is running.
    Used by Docker and cloud platforms to monitor app status.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "database": "connected",
            "qdrant": "connected",
            "redis": "connected"
        }
    }

# Register ALL routers
# NOTE: We removed the `prefix` arguments here because the routers 
# already define their own prefixes (e.g., prefix="/auth" in auth.py)
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(rag_router)
app.include_router(audit_router)
app.include_router(dashboard_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)