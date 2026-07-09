# 1. Use an official lightweight Python image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy ONLY the requirements file first (Docker Cache Optimization)
COPY requirements.txt .

# 4. Install CPU-only PyTorch to prevent massive 2.5GB CUDA downloads and timeouts
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 5. Install the rest of the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Automatically patch Ragas to prevent the VertexAI import error in Linux
# We read the file directly using its absolute path to avoid importing the broken library
RUN python -c "import pathlib; p=pathlib.Path('/usr/local/lib/python3.11/site-packages/ragas/llms/base.py'); t=p.read_text(); p.write_text(t.replace('from langchain_community.chat_models.vertexai import ChatVertexAI', 'class ChatVertexAI:\n    pass'))"

# 7. Download the spaCy English language model for Presidio (PII Guardrail)
RUN python -m spacy download en_core_web_lg

# 8. Copy the rest of the application code
COPY . .

# 9. Expose the port the app runs on
EXPOSE 8000

# 10. Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]