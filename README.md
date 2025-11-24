# ScholarFlow 

ScholarFlow is an **autonomous research workspace** built on top of a Retrieval-Augmented Generation (RAG) stack.

It combines:

- A **Research Agent** (planner → retriever → writer → critic)
- A **Knowledge Base** where you can upload PDFs and index them into a vector store
- An **Admin dashboard** to manage migrations and the vector database

The UI is built with **Streamlit**, the backend with **FastAPI + LangGraph**, and retrieval is powered by **Qdrant** (vector store) and **SentenceTransformers** embeddings. LLM calls are routed through **Groq**.

---

## Features

### Research Agent

- Chat-like research interface
- Multi-step agent pipeline:
  - **Planner**: decomposes your query into focused search queries
  - **Retriever**: hybrid retrieval over your indexed corpus
  - **Writer**: drafts a structured literature-style answer in Markdown
  - **Critic**: reviews the draft and returns a short verdict / revision hints
- Conversation history with:
  - Multiple saved conversations
  - Ability to reopen previous sessions from the sidebar
  - Per-response “Run details” panel (query, search plan, critic feedback)

---

### Knowledge Base

- Upload **PDF documents**
- Text is parsed and:
  - Split into passages
  - Embedded with `sentence-transformers`
  - Indexed into **Qdrant** under a configurable collection
- These indexed passages are used as the retrieval corpus for the Research Agent.

---

### Admin Dashboard

- View **migration status** of the vector store
- Trigger **vector DB reset** via the `/admin/clear_vector_db` endpoint
- Designed for local dev: helps you wipe & re-index quickly during iteration

---

## Architecture Overview

High-level components:

- **UI**: `ui.py`

  - Streamlit app
  - Modes: `Research Agent`, `Knowledge Base`, `Admin`
  - Talks to FastAPI over HTTP (`/generate`, `/upload`, `/admin/*`)

- **API**: `main.py`

  - FastAPI application (`api`)
  - Endpoints:
    - `POST /generate` – run the LangGraph workflow and return `review`, `critique`, `queries`
    - `POST /upload` – upload and index a PDF
    - `POST /admin/clear_vector_db` – clear Qdrant collection
    - `GET /admin/migration_status` – read migration worker status

- **Agent Orchestration**: `src/workflow.py`

  - Defines LangGraph `StateGraph`
  - Nodes: `Planner`, `Researcher`, `Writer`, `Critic`
  - Conditional loop for one or more revision cycles

- **Agents**: `src/agents/research_agents.py`

  - Wraps the Groq chat models
  - Implements `plan_research`, `retrieve`, `write`, `critique`

- **RAG Services**: `src/services/rag_service.py`

  - Hybrid retrieval over:
    - Vector store (Qdrant)
    - (Optionally) graph store (Neo4j) for author / paper relations
  - Returns combined context for the writer

- **Ingestion & Migration**:

  - `src/services/ingest_service.py` – handles PDF → text → embeddings → Qdrant (+ graph)
  - `src/services/migration_service.py` – background migration worker for schema updates

- **Persistence**:

  - `src/db/vector_store.py` – Qdrant client wrapper, schema checks, auto-migration, clear-collection helper
  - `src/db/graph_store.py` – Neo4j client wrapper (if used)

- **Config & Logging**:
  - `src/config.py` – environment-driven settings (API keys, URLs, model names, collection name)
  - `src/logger.py` – unified logger used across services

---
