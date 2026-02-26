# ScholarFlow

ScholarFlow is a production-style RAG workspace built with:

- `FastAPI` backend
- `Streamlit` control plane UI
- `LangGraph` multi-step agent workflow
- `Qdrant` vector retrieval + lightweight author graph expansion

The project is designed to demonstrate practical RAG engineering depth: retrieval diagnostics, grounded answer generation, answer quality scoring, ingestion operations, and admin controls.

## Core Capabilities

### 1. Research Assistant
- Planner -> Retriever -> Writer -> Critic workflow
- Configurable run modes: `fast`, `balanced`, `deep`
- Adjustable retrieval controls:
  - planner query budget
  - citation budget
  - score threshold
  - graph expansion toggle
- Response metadata:
  - token usage
  - latency
  - citation count
  - retrieval diagnostics

### 2. RAG Studio
- **Retrieval Inspector**
  - direct `/retrieve` calls
  - ranking and score visibility
  - context preview and diagnostics JSON
- **Answer Evaluator**
  - direct `/evaluate` scoring
  - grounding metrics and improvement suggestions
  - optional auto-retrieval context for evaluation
- **Prompt Arena**
  - side-by-side prompt comparison
  - latency/citation metrics for A/B prompt testing

### 3. Knowledge Base
- PDF ingestion (`/upload`)
- chunking + embedding + indexing into Qdrant
- corpus diagnostics:
  - collection vector count
  - paper count estimate
  - document/passage/embedding stats

### 4. Admin Operations
- migration status + restart
- vector DB reset
- logs + diagnostics panels
- system profile and health visibility

## API Surface

### Public
- `GET /health`
- `POST /generate`
- `POST /retrieve`
- `POST /evaluate`
- `POST /upload`

### Admin (token-gated when `ADMIN_API_TOKEN` is set)
- `GET /admin/stats`
- `GET /admin/collection_info`
- `GET /admin/paper_count`
- `GET /admin/migration_status`
- `POST /admin/restart_migration`
- `POST /admin/clear_vector_db`
- `GET /admin/logs`
- `GET /admin/system_info`
- `GET /admin/debug` (if enabled)

## Project Structure

- `ui.py` - Streamlit app
- `main.py` - FastAPI app
- `src/workflow.py` - LangGraph orchestration
- `src/agents/research_agents.py` - planner/writer/critic logic + fallbacks
- `src/services/rag_service.py` - hybrid retrieval, ranking, diagnostics
- `src/services/ingest_service.py` - PDF ingest pipeline
- `src/services/migration_service.py` - schema migration worker
- `src/db/vector_store.py` - Qdrant adapter
- `src/db/graph_store.py` - JSON graph store

## Run Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start backend:
```bash
uvicorn main:api --reload --port 8000
```

3. Start UI:
```bash
streamlit run ui.py
```

## Environment Variables

Set these in `.env` as needed:

- `GROQ_API_KEY`
- `ADMIN_API_TOKEN`
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `COLLECTION_NAME`
- `EMBEDDING_MODEL`
- `EMBEDDING_STRATEGY` (`auto` or `hashed`)
- `EMBEDDING_ALLOW_REMOTE_DOWNLOAD`
- `CORS_ALLOWED_ORIGINS`

## Notes

- If `GROQ_API_KEY` is missing, ScholarFlow falls back to deterministic planning/writing behavior so the app still runs.
- For production deployment, point `QDRANT_URL` to managed Qdrant and set strict CORS/admin token values.
