from sentence_transformers import SentenceTransformer
from typing import List

class Embedder:
    """
    Generates embeddings for text using the all-MiniLM-L6-v2 model.
    This model produces 384-dimensional vectors optimized for semantic search.
    """
    
    def __init__(self):
        """
        Initialize the embedding model.
        The model is downloaded and cached on first run.
        """
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Convert a list of texts into 384-dimensional embedding vectors.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (each vector is a list of 384 floats)
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()
    
    def embed_text(self, text: str) -> List[float]:
        """
        Convert a single text string into a 384-dimensional embedding vector.
        
        Args:
            text: The text string to embed
            
        Returns:
            Embedding vector (list of 384 floats)
        """
        return self.embed_texts([text])[0]