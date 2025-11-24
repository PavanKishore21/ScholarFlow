from typing import Any, Dict, List, Union
import io
import uuid

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader

from src.workflow import app as agent_app
from src.services.ingest_service import IngestService
from src.services.migration_service import MigrationService
from src.logger import get_logger

log = get_logger("Main")

api = FastAPI()
ingestor = IngestService()
migration_service = MigrationService()

# ----------------------------------------------------------
# CORS
# ----------------------------------------------------------
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------
# Startup — run migration in background
# ----------------------------------------------------------
@api.on_event("startup")
async def startup_event():
    log.info("🚀 FastAPI startup: launching background migration worker")
    migration_service.start_background_migration()


# ----------------------------------------------------------
# Request / response models
# ----------------------------------------------------------
class Request(BaseModel):
    topic: str


def _compute_token_count(text_or_list: Union[str, List[str], None]) -> int:
    """Very simple token proxy: count whitespace-separated words."""
    if text_or_list is None:
        return 0
    if isinstance(text_or_list, str):
        return len(text_or_list.split())
    if isinstance(text_or_list, list):
        return sum(len(str(t).split()) for t in text_or_list)
    return 0


# ----------------------------------------------------------
# Main research endpoint
# ----------------------------------------------------------
@api.post("/generate")
def generate_review(req: Request):
    """
    Call the research workflow and return:
    - review      : final draft text
    - critique    : self-critique
    - queries     : search plan
    - stats       : simple token stats for LLM vs retrieved text
    - citations   : list of {title, url, snippet} used to build clickable refs
    """
    init_state: Dict[str, Any] = {"task": req.topic, "revision_count": 0}
    result: Dict[str, Any] = agent_app.invoke(init_state)

    draft = result.get("draft", "") or ""
    critique = result.get("critique", "") or ""
    plan = result.get("plan", []) or []

    # --- retrieved context, if your workflow exposes it ---
    # Adjust these keys to match your workflow structure.
    retrieved_context = (
        result.get("retrieved_context")
        or result.get("context")
        or result.get("retrieval", "")
    )

    llm_tokens = _compute_token_count(draft)
    retrieved_tokens = _compute_token_count(retrieved_context)

    # --- citations / references ---
    raw_citations = (
        result.get("citations")
        or result.get("sources")
        or result.get("references")
        or []
    )

    citations: List[Dict[str, str]] = []
    for c in raw_citations:
        if isinstance(c, dict):
            citations.append(
                {
                    "title": str(
                        c.get("title")
                        or c.get("name")
                        or c.get("paper_id")
                        or "Source"
                    ),
                    "url": str(c.get("url") or c.get("link") or ""),
                    "snippet": str(
                        c.get("snippet")
                        or c.get("text")
                        or c.get("preview", "")
                    ),
                }
            )
        else:
            # string fallback
            citations.append(
                {"title": str(c), "url": "", "snippet": ""}
            )

    return {
        "review": draft,
        "critique": critique,
        "queries": plan,
        "stats": {
            "llm_tokens": llm_tokens,
            "retrieved_tokens": retrieved_tokens,
        },
        "citations": citations,
    }


# ----------------------------------------------------------
# Upload PDF — basic ingestion
# ----------------------------------------------------------
@api.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    content = await file.read()
    reader = PdfReader(io.BytesIO(content))
    extracted = ""

    for page in reader.pages:
        extracted += page.extract_text() or ""

    title = file.filename.replace(".pdf", "")
    paper_id = str(uuid.uuid4())[:8]

    ingestor.ingest_text(
        paper_id=paper_id,
        title=title,
        text=extracted,
        source="Upload",
    )

    return {
        "status": "indexed",
        "title": title,
        "paper_id": paper_id,
    }


# ----------------------------------------------------------
# Admin — clear vector DB
# ----------------------------------------------------------
@api.post("/admin/clear_vector_db")
def clear_vector_db():
    ingestor.vs.clear_collection()

    migration_service.running = False
    migration_service.finished = False
    migration_service.migrated = 0
    migration_service.errors = 0

    return {"status": "cleared"}


# ----------------------------------------------------------
# Admin — migration status
# ----------------------------------------------------------
@api.get("/admin/migration_status")
def migration_status():
    return {
        "running": migration_service.running,
        "finished": migration_service.finished,
        "migrated": migration_service.migrated,
        "errors": migration_service.errors,
        # simple uptime string if your MigrationService exposes it, else N/A
        "uptime": getattr(migration_service, "uptime", "N/A"),
    }


# ----------------------------------------------------------
# Admin — restart migration
# ----------------------------------------------------------
@api.post("/admin/restart_migration")
def restart_migration():
    migration_service.start_background_migration()
    return {"status": "restarted"}


# ----------------------------------------------------------
# Admin — corpus stats for Knowledge Base sidebar
# ----------------------------------------------------------
@api.get("/admin/stats")
def corpus_stats():
    """
    Returns simple stats used by the Knowledge Base view.
    If your IngestService exposes better stats, wire them here.
    """
    try:
        # Example if you later add a proper method:
        # stats = ingestor.get_stats()
        # return stats
        pass
    except Exception:
        # fall through to default
        ...

    return {
        "documents": getattr(ingestor, "documents_count", 0),
        "passages": getattr(ingestor, "passages_count", 0),
        "embeddings": getattr(ingestor, "embeddings_count", 0),
    }


# ----------------------------------------------------------
# Admin — recent logs (simple stub)
# ----------------------------------------------------------
@api.get("/admin/logs")
def admin_logs():
    """
    Return recent activity logs for the Admin screen.
    If MigrationService tracks logs, expose them here.
    """
    logs = getattr(migration_service, "logs", [])
    # Expect each log to be {timestamp, level, message}. If not, fall back.
    normalized: List[Dict[str, str]] = []
    for entry in logs:
        if isinstance(entry, dict):
            normalized.append(
                {
                    "timestamp": str(entry.get("timestamp", "")),
                    "level": str(entry.get("level", "info")),
                    "message": str(entry.get("message", "")),
                }
            )
        else:
            normalized.append(
                {
                    "timestamp": "",
                    "level": "info",
                    "message": str(entry),
                }
            )

    return {"logs": normalized}


# ----------------------------------------------------------
# Admin — system info
# ----------------------------------------------------------
@api.get("/admin/system_info")
def system_info():
    return {
        "version": "0.1.0",
        "vector_db": getattr(getattr(ingestor, "vs", None), "name", "Qdrant"),
        "embedding_model": getattr(
            ingestor, "embedding_model_name", "Unknown"
        ),
    }


# ----------------------------------------------------------
# Run
# ----------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(api, host="0.0.0.0", port=8000)
