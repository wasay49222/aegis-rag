from fastapi import FastAPI

# Initialize the FastAPI application
app = FastAPI(title="Aegis-RAG Enterprise API")

@app.get("/health")
def health_check():
    """
    Health check endpoint to verify the server is running.
    Used by Docker and cloud platforms to monitor app status.
    """
    return {"status": "healthy"}