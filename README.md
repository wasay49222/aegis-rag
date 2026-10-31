# Aegis-RAG
## Document retrieval and generative AI prototype

A student portfolio project exploring retrieval-augmented generation (RAG): upload documents, retrieve relevant passages, and generate a response with a local language model. The project combines a FastAPI backend, a Next.js interface, Qdrant vector storage, PostgreSQL, and input/output guardrail components.

## Implementation

| Component | Current implementation |
| --- | --- |
| Document ingestion | PDF/TXT parsing, text chunking, MiniLM embeddings, document metadata, and Qdrant storage. |
| Retrieval | Dense-vector similarity search, filtered by user and optionally document. Hybrid/BM25 search is not implemented. |
| Answer generation | Retrieved passages are supplied to `llama3.2:1b` through Ollama. |
| Authentication | JWT-based authentication is integrated into document and query routes. |
| Guardrails | Microsoft Presidio redaction and a pretrained prompt-injection classifier are called by the query pipeline. These components do not guarantee detection of every attack or sensitive value. |
| Activity records | Query and security-event records are stored in PostgreSQL. These are ordinary database records, not immutable logs. |
| Interface | Login, document management, querying, audit views, and dashboard components are present. |

### Workflow

1. Upload a document and split its extracted text into chunks.
2. Generate embeddings and store vectors with document/user metadata.
3. Check and redact a submitted question, then retrieve relevant chunks.
4. Generate a response through local Ollama and apply output redaction.
5. Return the answer and retrieved text, and record query activity.

Key code: [ingestion](backend/app/api/documents.py), [vector retrieval](backend/app/services/vector_store.py), [RAG pipeline](backend/app/services/rag.py), [query route](backend/app/api/rag.py).

## Experimental and unfinished features

- **Answer critic:** LangGraph researcher/critic nodes and conditional edges exist, but [the critic currently returns `APPROVED` unconditionally](backend/app/services/agents/graph.py). Factual validation and critique-driven retries are not active.
- **Evaluation:** [Ragas evaluation code](backend/app/services/evaluation.py) and a [standalone evaluation script](backend/scripts/run_evaluation.py) exist. The live query route does not schedule the evaluator.
- **Dashboard scores:** [The dashboard](backend/app/api/dashboard.py) falls back to 0.91, 0.87, and 0.89 when evaluation data is absent. These are preset values, not verified quality benchmarks.
- **Authorization:** Retrieval filters are present, but [audit endpoints](backend/app/api/audit.py) do not currently require authentication or filter records by user. Complete application-wide isolation and role-based access enforcement are not established.
- **Sensitive logging:** Some records retain original questions. Redaction before generation does not mean all stored data is redacted.
- **Deployment:** Docker configuration and workflow files are included, but they are not evidence of a working deployment. The backend database connection is hardcoded to localhost, which needs adjustment for container-to-container access. The direct CI workflow is empty; another definition is nested under an extra workflow directory.
- **Health endpoint:** Service status labels are static and do not probe live dependencies.

This is a development prototype. It has not been established as production-ready, compliant with any security standard, or resistant to all hallucinations and attacks. No reproduced accuracy or evaluation results are claimed here.

## Local development

Prerequisites: Python 3.11+, Node.js with npm, Docker Compose, and Ollama. The following is the intended host-based development sequence; a clean end-to-end run has not been verified as part of this documentation update.

From the repository root, start the database and vector service:

```bash
docker compose up -d postgres qdrant
ollama pull llama3.2:1b
```

Keep Ollama running locally. In a Python virtual environment:

```bash
cd backend
pip install -r requirements.txt
python init_db.py
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the frontend at http://localhost:3000 and API documentation at http://localhost:8000/docs.

Check [database configuration](backend/app/database.py), [vector-store settings](backend/app/services/vector_store.py), and [Ollama configuration](backend/app/services/rag.py) before running. The initialization script creates an `aegis_chunks` collection, whereas the active vector store uses `aegis_documents`; confirm the active collection is initialized before ingestion. Use the authentication API/UI rather than assuming a default account exists.

## Next improvements

- Implement meaningful critic checks and connect evaluation to the query lifecycle.
- Replace preset dashboard scores with a clear unavailable state when results are absent.
- Enforce authentication and ownership consistently, and review sensitive log retention.
- Consolidate configuration and correct Docker/CI setup.
- Add reproducible evaluation outputs and verify a clean local demonstration.

## Author

Syed Muhammad Wasay — BS Artificial Intelligence student, ITU Lahore.

[GitHub](https://github.com/wasay49222) | [LinkedIn](https://www.linkedin.com/in/syed-muhammad-wasay-119682289)

## License

[MIT](LICENSE)

