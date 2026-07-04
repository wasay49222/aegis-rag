from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router

# Initialize the FastAPI application
app = FastAPI(title="Aegis-RAG Enterprise API")

@app.get("/health")
def health_check():
    """
    Health check endpoint to verify the server is running.
    Used by Docker and cloud platforms to monitor app status.
    """
    return {"status": "healthy"}

# Register the auth routes
app.include_router(auth_router)

# Register the documents routes
app.include_router(documents_router)