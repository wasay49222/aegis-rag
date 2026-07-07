import uuid
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

class VectorStore:
    def __init__(self):
        # Connect to the local Qdrant Docker container
        self.client = QdrantClient(host="localhost", port=6333)
        self.collection_name = "aegis_documents"
        self.vector_size = 384 # Must match the embedder output

    def initialize_collection(self):
        """
        Creates the Qdrant collection if it doesn't already exist.
        Uses Cosine similarity, which is the industry standard for text embeddings.
        """
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
            )
            print(f"Created Qdrant collection: {self.collection_name}")
        else:
            print(f"Qdrant collection '{self.collection_name}' already exists.")

    def insert_chunks(self, chunks_data: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        Inserts chunks and their corresponding embeddings into Qdrant.
        """
        points = []
        for i, (chunk, vector) in enumerate(zip(chunks_data, embeddings)):
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload=chunk
                )
            )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"Inserted {len(points)} vectors into Qdrant.")

    def search(self, query_embedding: List[float], top_k: int = 5, user_id: str = None, document_id: str = None) -> List[Dict[str, Any]]:
        """
        Searches Qdrant for the most similar chunks.
        Enforces security by filtering results by user_id and document_id.
        """
        # Build the security filter (Vector-level Row-Level Security)
        must_conditions = []
        if user_id:
            must_conditions.append(models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)))
        if document_id:
            must_conditions.append(models.FieldCondition(key="document_id", match=models.MatchValue(value=document_id)))
        
        search_filter = models.Filter(must=must_conditions) if must_conditions else None

        # Perform the search using query_points (the modern Qdrant API)
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=top_k,
            query_filter=search_filter,
            with_payload=True
        )
        
        # Extract the payload (the text and metadata) from the response
        return [point.payload for point in search_result.points]