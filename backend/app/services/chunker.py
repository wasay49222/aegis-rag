import tiktoken
import re
from typing import List

# Initialize the tokenizer (cl100k_base is used by OpenAI and works well for MiniLM)
tokenizer = tiktoken.get_encoding("cl100k_base")

def chunk_fixed_size(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Splits text into chunks of exactly N tokens, with a sliding window overlap.
    """
    tokens = tokenizer.encode(text)
    chunks = []
    start = 0
    
    while start < len(tokens):
        end = start + chunk_size
        # Extract the slice of tokens and decode it back to text
        chunk_text = tokenizer.decode(tokens[start:end])
        chunks.append(chunk_text)
        
        # Move the start pointer forward, minus the overlap to ensure continuity
        start += (chunk_size - overlap)
        
    return chunks

def chunk_recursive(text: str, max_chunk_size: int = 2000) -> List[str]:
    """
    Splits text hierarchically: Paragraphs -> Sentences -> Words.
    Improved to handle PDF extraction quirks (single newlines).
    """
    # PDFs often use single newlines instead of double newlines
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        # If adding this paragraph exceeds our character limit
        if len(current_chunk) + len(para) > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # If the paragraph itself is too big, split it by sentences
            if len(para) > max_chunk_size:
                sentences = re.split(r'(?<=[.!?]) +', para)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > max_chunk_size:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += " " + sentence if current_chunk else sentence
            else:
                current_chunk = para
        else:
            current_chunk += " " + para if current_chunk else para
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def chunk_semantic(text: str) -> List[str]:
    """
    Placeholder for Semantic Chunking.
    True semantic chunking requires calculating embeddings for every sentence 
    and splitting where the cosine similarity drops (indicating a topic change).
    We will integrate the Embedder from Level 5 to fully implement this.
    For now, it falls back to sentence splitting.
    """
    # Simple sentence boundary detection
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > 1000:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += " " + sentence if current_chunk else sentence
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks