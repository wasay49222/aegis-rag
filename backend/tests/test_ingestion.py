import pytest
from app.services.document_parser import extract_text
from app.services.chunker import chunk_fixed_size, chunk_recursive

# --- Parser Tests ---
def test_extract_text_from_txt(tmp_path):
    """Test that we can extract text from a plain text file."""
    # Create a dummy text file in a temporary folder
    dummy_file = tmp_path / "test.txt"
    dummy_file.write_text("Hello world. This is a test.")
    
    text = extract_text(str(dummy_file))
    assert text == "Hello world. This is a test."

def test_extract_text_unsupported_format(tmp_path):
    """Test that the parser blocks unsupported file types."""
    dummy_file = tmp_path / "test.docx"
    dummy_file.write_text("fake doc")
    
    with pytest.raises(Exception) as exc_info:
        extract_text(str(dummy_file))
    
    # Verify it throws our specific 400 error
    assert exc_info.value.status_code == 400

# --- Chunker Tests ---
def test_chunk_fixed_size():
    """Test that fixed-size chunking creates overlapping slices."""
    # Simple text where 1 word roughly equals 1 token
    text = "one two three four five six seven eight nine ten"
    
    # Chunk by 3 tokens, with 1 token overlap
    chunks = chunk_fixed_size(text, chunk_size=3, overlap=1)
    
    assert len(chunks) > 1
    assert "one" in chunks[0]
    assert "two" in chunks[0]
    assert "three" in chunks[0]
    # The overlap should ensure 'three' appears in the next chunk too
    assert "three" in chunks[1] 

def test_chunk_recursive():
    """Test that recursive chunking respects paragraph breaks."""
    text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
    
    chunks = chunk_recursive(text)
    
    assert len(chunks) >= 1
    assert "Paragraph one" in chunks[0]