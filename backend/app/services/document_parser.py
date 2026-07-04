import fitz  # PyMuPDF
from pathlib import Path
from fastapi import HTTPException

def extract_text(file_path: str) -> str:
    """
    Extracts text from a PDF or plain text file.
    """
    path = Path(file_path)
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Handle Plain Text files
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8")

    # Handle PDF files
    if path.suffix.lower() == ".pdf":
        text = ""
        # Open the PDF
        doc = fitz.open(path)
        # Iterate through every page and extract text
        for page_num in range(len(doc)):
            page = doc[page_num]
            text += page.get_text()
        doc.close()
        return text

    # Reject unsupported formats
    raise HTTPException(status_code=400, detail="Unsupported file format. Please upload .pdf or .txt")