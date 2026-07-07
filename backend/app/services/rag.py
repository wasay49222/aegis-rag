import httpx
from typing import List, Dict, Any

from app.services.embedder import Embedder
from app.services.vector_store import VectorStore

class RAGPipeline:
    def __init__(self):
        # Initialize our existing services
        self.embedder = Embedder()
        self.vector_store = VectorStore()
        
        # Ollama local API configuration
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "llama3.2:1b"

    def retrieve(self, query: str, user_id: str, document_id: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        1. Embeds the user's query.
        2. Searches Qdrant for the most relevant chunks.
        3. Returns the text and metadata of those chunks.
        """
        # Turn the question into 384-dimensional math
        query_embedding = self.embedder.embed_text(query)
        
        # Search Qdrant, enforcing security (user_id)
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            user_id=user_id,
            document_id=document_id
        )
        return results

    def generate_answer(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Takes the retrieved context and the user's question, 
        builds a prompt, and asks Llama 3 for the answer.
        """
        # 1. Combine the text from the retrieved chunks into one string
        context_text = "\n\n---\n\n".join([chunk.get("text", "") for chunk in context_chunks])
        
        # 2. Build the Prompt (The "Instruction" to the AI)
        prompt = f"""Use the following context to answer the question. 
If the answer is not in the context, say 'I don't know.'

Context: 
{context_text}

Question: {query}

Answer:"""
        
               # 3. Call the local Ollama API
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 150  # Limit response to ~150 tokens to prevent long generation times
            }
        }
        
        # Increased timeout to 5 minutes (300 seconds) for slower CPUs
        response = httpx.post(self.ollama_url, json=payload, timeout=300.0)
        response.raise_for_status()
        
        # Extract the text answer from Ollama's JSON response
        return response.json().get("response", "I couldn't generate an answer.")