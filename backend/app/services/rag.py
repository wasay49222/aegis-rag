import httpx
from typing import List, Dict, Any, Tuple

from app.services.embedder import Embedder
from app.services.vector_store import VectorStore
from app.services.pii_guardrail import PIIGuardrail

class RAGPipeline:
    def __init__(self):
        # Initialize our existing services
        self.embedder = Embedder()
        self.vector_store = VectorStore()
        self.guardrail = PIIGuardrail() # Initialize the security shield
        
        # Ollama local API configuration
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "llama3.2:1b"

    def retrieve(self, query: str, user_id: str, document_id: str = None, top_k: int = 5) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """
        1. Sanitizes the query for PII.
        2. Embeds the clean query.
        3. Searches Qdrant.
        """
        # SECURITY: Redact PII before processing
        clean_query, pii_audit_log = self.guardrail.redact(query)
        
        print(f"[GUARDRAIL] Original Query: {query}")
        print(f"[GUARDRAIL] Sanitized Query: {clean_query}")
        
        # Turn the CLEAN question into 384-dimensional math
        query_embedding = self.embedder.embed_text(clean_query)
        
        # Search Qdrant, enforcing security (user_id)
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            user_id=user_id,
            document_id=document_id
        )
        # Return both the results AND the audit log
        return results, pii_audit_log

    def generate_answer(self, query: str, context_chunks: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, str]]]:
        """
        Takes the retrieved context and the user's question, 
        builds a prompt, asks Llama 3, and sanitizes the output.
        """
        # 1. Combine the text from the retrieved chunks into one string
        context_text = "\n\n---\n\n".join([chunk.get("text", "") for chunk in context_chunks])
        
        # SECURITY: Redact PII from the retrieved context just in case the PDF contained PII
        clean_context, context_pii_log = self.guardrail.redact(context_text)
        
        # 2. Build the Prompt
        prompt = f"""Use the following context to answer the question. 
If the answer is not in the context, say 'I don't know.'

Context: 
{clean_context}

Question: {query}

Answer:"""
        
        # 3. Call the local Ollama API
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 150
            }
        }
        
        response = httpx.post(self.ollama_url, json=payload, timeout=300.0)
        response.raise_for_status()
        raw_answer = response.json().get("response", "I couldn't generate an answer.")
        
        # SECURITY: Sanitize the LLM's final answer (Output Guardrail)
        clean_answer, answer_pii_log = self.guardrail.redact(raw_answer)
        
        # Combine all audit logs
        all_pii_logs = context_pii_log + answer_pii_log
        
        return clean_answer, all_pii_logs