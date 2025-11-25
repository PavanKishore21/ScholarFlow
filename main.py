from typing import Any, Dict, List, Union
import io
import uuid
import sys
import traceback

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader

from src.workflow import app as agent_app
from src.services.ingest_service import IngestService
from src.services.migration_service import MigrationService
from src.logger import get_logger

log = get_logger("Main")

# ----------------------------------------------------------
# FastAPI app (this is what Render loads as main:api)
# ----------------------------------------------------------
api = FastAPI(title="ScholarFlow API")

# We'll initialize these on startup instead of at import time
ingestor: IngestService | None = None
migration_service: MigrationService | None = None
startup_error: str | None = None

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
# Health check - now reports startup status
# ----------------------------------------------------------
@api.get("/health")
def healthcheck():
    if startup_error:
        return {
            "status": "degraded",
            "error": startup_error,
            "ingestor": ingestor is not None,
            "migration_service": migration_service is not None,
        }
    return {
        "status": "ok",
        "ingestor": ingestor is not None,
        "migration_service": migration_service is not None,
    }

# ----------------------------------------------------------
# Startup — init services & run migration in background
# ----------------------------------------------------------
@api.on_event("startup")
async def startup_event():
    global ingestor, migration_service, startup_error

    log.info("🚀 FastAPI startup: initializing services")
    print("🚀 FastAPI startup: initializing services", file=sys.stderr)

    # Initialize IngestService
    try:
        if ingestor is None:
            log.info("Initializing IngestService...")
            print("Initializing IngestService...", file=sys.stderr)
            ingestor = IngestService()
            log.info("✅ IngestService initialized")
            print("✅ IngestService initialized", file=sys.stderr)
    except Exception as e:
        error_msg = f"Failed to initialize IngestService: {e}"
        log.exception(error_msg)
        print(f"❌ {error_msg}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        startup_error = error_msg
        # Don't return - continue with partial initialization

    # Initialize MigrationService
    try:
        if migration_service is None:
            log.info("Initializing MigrationService...")
            print("Initializing MigrationService...", file=sys.stderr)
            migration_service = MigrationService()
            log.info("✅ MigrationService initialized")
            print("✅ MigrationService initialized", file=sys.stderr)
            
            # Start background migration
            migration_service.start_background_migration()
            log.info("🚀 Started background migration worker")
            print("🚀 Started background migration worker", file=sys.stderr)
    except Exception as e:
        error_msg = f"Failed to initialize MigrationService: {e}"
        log.exception(error_msg)
        print(f"❌ {error_msg}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        if startup_error:
            startup_error += f"; {error_msg}"
        else:
            startup_error = error_msg

    # Final startup status
    if startup_error:
        print(f"⚠️  Server started with errors: {startup_error}", file=sys.stderr)
    else:
        print("✅ All services initialized successfully", file=sys.stderr)

# ----------------------------------------------------------
# Models & helpers
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
    - citations   : list of {title, url, snippet} for clickable refs
    """
    try:
        init_state: Dict[str, Any] = {"task": req.topic, "revision_count": 0}
        result: Dict[str, Any] = agent_app.invoke(init_state)

        draft = result.get("draft", "") or ""
        critique = result.get("critique", "") or ""
        plan = result.get("plan", []) or []

        # retrieved context, if your workflow exposes it
        retrieved_context = (
            result.get("retrieved_context")
            or result.get("context")
            or result.get("retrieval", "")
        )

        llm_tokens = _compute_token_count(draft)
        retrieved_tokens = _compute_token_count(retrieved_context)

        # citations / references (best-effort normalization)
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
                citations.append({"title": str(c), "url": "", "snippet": ""})

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
    except Exception as e:
        log.exception(f"Error generating review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate review: {str(e)}"
        )

# ----------------------------------------------------------
# Upload PDF — basic ingestion
# ----------------------------------------------------------
@api.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if ingestor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingest service not initialized. Check /health for details.",
        )

    try:
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
    except Exception as e:
        log.exception(f"Error uploading PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload PDF: {str(e)}"
        )

# ----------------------------------------------------------
# Admin — clear vector DB
# ----------------------------------------------------------
@api.post("/admin/clear_vector_db")
def clear_vector_db():
    if ingestor is None or getattr(ingestor, "vs", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store not initialized",
        )

    try:
        ingestor.vs.clear_collection()

        if migration_service is not None:
            migration_service.running = False
            migration_service.finished = False
            migration_service.migrated = 0
            migration_service.errors = 0

        return {"status": "cleared"}
    except Exception as e:
        log.exception(f"Error clearing vector DB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear vector DB: {str(e)}"
        )

# ----------------------------------------------------------
# Admin — migration status
# ----------------------------------------------------------
@api.get("/admin/migration_status")
def migration_status():
    if migration_service is None:
        return {
            "running": False,
            "finished": False,
            "migrated": 0,
            "errors": 0,
            "uptime": "N/A",
            "message": "Migration service not initialized"
        }

    return {
        "running": migration_service.running,
        "finished": migration_service.finished,
        "migrated": migration_service.migrated,
        "errors": migration_service.errors,
        "uptime": getattr(migration_service, "uptime", "N/A"),
    }

# ----------------------------------------------------------
# Admin — restart migration
# ----------------------------------------------------------
@api.post("/admin/restart_migration")
def restart_migration():
    if migration_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Migration service not initialized",
        )

    try:
        migration_service.start_background_migration()
        return {"status": "restarted"}
    except Exception as e:
        log.exception(f"Error restarting migration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart migration: {str(e)}"
        )

# ----------------------------------------------------------
# Admin — corpus stats for Knowledge Base
# ----------------------------------------------------------
@api.get("/admin/stats")
def corpus_stats():
    if ingestor is None:
        return {
            "documents": 0,
            "passages": 0,
            "embeddings": 0,
            "message": "Ingestor not initialized"
        }

    return {
        "documents": getattr(ingestor, "documents_count", 0),
        "passages": getattr(ingestor, "passages_count", 0),
        "embeddings": getattr(ingestor, "embeddings_count", 0),
    }

# ----------------------------------------------------------
# Admin — recent logs
# ----------------------------------------------------------
@api.get("/admin/logs")
def admin_logs():
    if migration_service is None:
        return {"logs": [], "message": "Migration service not initialized"}

    logs = getattr(migration_service, "logs", [])
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
                {"timestamp": "", "level": "info", "message": str(entry)}
            )

    return {"logs": normalized}


# ----------------------------------------------------------
# Debug endpoint to check environment
# ----------------------------------------------------------
@api.get("/admin/debug")
def debug_info():
    """Returns debug information about the service state."""
    import os
    
    return {
        "startup_error": startup_error,
        "ingestor_initialized": ingestor is not None,
        "migration_service_initialized": migration_service is not None,
        "environment_vars": {
            "PORT": os.environ.get("PORT", "not set"),
            # Add other non-sensitive env vars you want to check
        },
        "python_version": sys.version,
    }