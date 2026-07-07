from app.services.vector_store import VectorStore

# Initialize the vector store
vs = VectorStore()

# Scroll through all points in the collection
result = vs.client.scroll(
    collection_name="aegis_documents",
    limit=5,
    with_payload=True
)

print(f"Found {len(result[0])} points in Qdrant:\n")
for i, point in enumerate(result[0]):
    print(f"--- Point {i+1} ---")
    print(f"ID: {point.id}")
    print(f"Payload: {point.payload}")
    print(f"Text length: {len(point.payload.get('text', ''))}")
    print()