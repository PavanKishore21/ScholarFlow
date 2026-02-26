from __future__ import annotations

import io
import re
import sys
import time
import traceback
from typing import Any, Dict, List, Union

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pypdf import PdfReader

from src.config import settings
from src.logger import get_logger
from src.services.ingest_service import IngestService
from src.services.migration_service import MigrationService
from src.services.rag_service import RAGService
from src.workflow import app as agent_app

log = get_logger("Main")

api = FastAPI(title="ScholarFlow API")

ingestor: IngestService | None = None
migration_service: MigrationService | None = None
rag_service: RAGService | None = None
startup_error: str | None = None


def _cors_origins() -> List[str]:
    raw = (settings.CORS_ALLOWED_ORIGINS or "*").strip()
    if raw == "*":
        return ["*"]
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts or ["*"]


api.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=2000)
    mode: str = Field(default="balanced")
    max_plan_queries: int | None = Field(default=None, ge=1, le=6)
    max_citations: int | None = Field(default=None, ge=3, le=30)
    score_threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    include_graph: bool = True
    include_diagnostics: bool = True


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    top_k: int = Field(default=8, ge=1, le=30)
    score_threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    include_graph: bool = True
    retrieval_mode: str = Field(default="balanced")


class EvaluateRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    answer: str = Field(min_length=1, max_length=40_000)
    context: str = Field(default="", max_length=60_000)


class Request(BaseModel):
    topic: str = Field(min_length=2, max_length=2000)


def _compute_token_count(text_or_list: Union[str, List[str], None]) -> int:
    if text_or_list is None:
        return 0
    if isinstance(text_or_list, str):
        return len(text_or_list.split())
    if isinstance(text_or_list, list):
        return sum(len(str(t).split()) for t in text_or_list)
    return 0


def _normalize_mode(mode: str | None) -> str:
    value = str(mode or "balanced").strip().lower()
    if value not in {"fast", "balanced", "deep"}:
        return "balanced"
    return value


def _mode_defaults(mode: str) -> Dict[str, Any]:
    if mode == "fast":
        return {"plan": 2, "citations": 6, "retrieval_mode": "focused"}
    if mode == "deep":
        return {"plan": 5, "citations": 14, "retrieval_mode": "broad"}
    return {"plan": 3, "citations": 9, "retrieval_mode": "balanced"}


def _require_ingestor() -> IngestService:
    if ingestor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingest service not initialized. Check /health for details.",
        )
    return ingestor


def _require_rag() -> RAGService:
    if rag_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service not initialized. Check /health for details.",
        )
    return rag_service


def _admin_guard(x_admin_token: str | None = Header(default=None)) -> None:
    required = settings.ADMIN_API_TOKEN
    if required and x_admin_token != required:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )


def _format_citations(raw_citations: Any, limit: int) -> List[Dict[str, Any]]:
    citations: List[Dict[str, Any]] = []
    for c in raw_citations or []:
        if isinstance(c, dict):
            citations.append(
                {
                    "title": str(c.get("title") or c.get("name") or c.get("paper_id") or "Source"),
                    "url": str(c.get("url") or c.get("link") or ""),
                    "snippet": str(c.get("snippet") or c.get("text") or c.get("preview", "")),
                    "source": str(c.get("source") or "Vector"),
                    "paper_id": str(c.get("paper_id") or ""),
                    "chunk_index": int(c.get("chunk_index") or 0),
                    "score": float(c.get("score", 0.0) or 0.0),
                    "rank": int(c.get("rank") or 0),
                }
            )
        else:
            citations.append(
                {
                    "title": str(c),
                    "url": "",
                    "snippet": "",
                    "source": "Vector",
                    "paper_id": "",
                    "chunk_index": 0,
                    "score": 0.0,
                    "rank": 0,
                }
            )
    return citations[:limit]


def _tokenize_eval(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9]{3,}", (text or "").lower())


def _split_sentences(text: str) -> List[str]:
    pieces = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return [p.strip() for p in pieces if p.strip()]


def _evaluate_answer(question: str, answer: str, context: str) -> Dict[str, Any]:
    answer_tokens = _tokenize_eval(answer)
    question_tokens = _tokenize_eval(question)
    context_tokens = _tokenize_eval(context)

    answer_vocab = set(answer_tokens)
    question_vocab = set(question_tokens)
    context_vocab = set(context_tokens)

    overlap = answer_vocab.intersection(context_vocab)
    grounding_coverage = len(overlap) / max(1, len(answer_vocab))

    question_alignment = len(answer_vocab.intersection(question_vocab)) / max(1, len(question_vocab))

    sentences = _split_sentences(answer)
    grounded_sentences = 0
    for sent in sentences:
        sent_vocab = set(_tokenize_eval(sent))
        if not sent_vocab:
            continue
        sent_overlap_ratio = len(sent_vocab.intersection(context_vocab)) / max(1, len(sent_vocab))
        if sent_overlap_ratio >= 0.2:
            grounded_sentences += 1
    grounded_sentence_ratio = grounded_sentences / max(1, len(sentences))

    citation_markers = len(re.findall(r"\[\d+\]", answer))

    overall_score = round(
        (0.45 * grounded_sentence_ratio + 0.35 * grounding_coverage + 0.20 * question_alignment) * 100,
        1,
    )
    if overall_score >= 80:
        verdict = "strong"
    elif overall_score >= 60:
        verdict = "good"
    elif overall_score >= 40:
        verdict = "needs_improvement"
    else:
        verdict = "weak"

    suggestions: List[str] = []
    if citation_markers == 0:
        suggestions.append("Add inline citations like [1], [2] for key claims.")
    if grounding_coverage < 0.25:
        suggestions.append("Increase retrieval depth or lower score threshold to improve evidence coverage.")
    if grounded_sentence_ratio < 0.5:
        suggestions.append("Reduce unsupported claims and tie each section to retrieved evidence.")
    if question_alignment < 0.2:
        suggestions.append("Refocus the answer on the original question objectives.")

    return {
        "overall_score": overall_score,
        "verdict": verdict,
        "grounding_coverage": round(grounding_coverage, 3),
        "grounded_sentence_ratio": round(grounded_sentence_ratio, 3),
        "question_alignment": round(question_alignment, 3),
        "citation_markers": citation_markers,
        "sentence_count": len(sentences),
        "suggestions": suggestions,
    }


@api.get("/")
def root():
    return {"status": "ok", "service": "scholarflow-api"}


@api.get("/health")
def healthcheck():
    return {
        "status": "degraded" if startup_error else "ok",
        "error": startup_error,
        "ingestor": ingestor is not None,
        "vector_store": bool(ingestor and ingestor.vs.available),
        "migration_service": migration_service is not None,
        "rag_service": rag_service is not None,
    }


@api.on_event("startup")
async def startup_event():
    global ingestor, migration_service, rag_service, startup_error

    startup_error = None
    errors = []

    log.info("FastAPI startup: initializing services")
    print("FastAPI startup: initializing services", file=sys.stderr)

    try:
        if ingestor is None:
            ingestor = IngestService()
            log.info("IngestService initialized")
    except Exception as e:
        err = f"Failed to initialize IngestService: {e}"
        log.exception(err)
        print(traceback.format_exc(), file=sys.stderr)
        errors.append(err)

    try:
        if migration_service is None:
            migration_service = MigrationService()
            migration_service.start_background_migration()
            log.info("MigrationService initialized")
    except Exception as e:
        err = f"Failed to initialize MigrationService: {e}"
        log.exception(err)
        print(traceback.format_exc(), file=sys.stderr)
        errors.append(err)

    try:
        if rag_service is None:
            rag_service = RAGService()
            log.info("RAGService initialized")
    except Exception as e:
        err = f"Failed to initialize RAGService: {e}"
        log.exception(err)
        print(traceback.format_exc(), file=sys.stderr)
        errors.append(err)

    if errors:
        startup_error = "; ".join(errors)


@api.post("/generate")
def generate_review(req: GenerateRequest):
    try:
        start = time.perf_counter()
        mode = _normalize_mode(req.mode)
        defaults = _mode_defaults(mode)

        max_plan_queries = int(req.max_plan_queries or defaults["plan"])
        max_citations = int(req.max_citations or defaults["citations"])
        retrieval_mode = defaults["retrieval_mode"]

        init_state: Dict[str, Any] = {
            "task": req.topic.strip(),
            "mode": retrieval_mode,
            "max_plan_queries": max_plan_queries,
            "max_citations": max_citations,
            "score_threshold": float(req.score_threshold or 0.0),
            "include_graph": bool(req.include_graph),
            "revision_count": 0,
        }
        result: Dict[str, Any] = agent_app.invoke(init_state)

        draft = result.get("draft", "") or ""
        critique = result.get("critique", "") or ""
        plan = result.get("plan", []) or []
        retrieval_meta = result.get("retrieval_meta", {}) or {}

        retrieved_context = result.get("context", "") or ""

        llm_tokens = _compute_token_count(draft)
        retrieved_tokens = _compute_token_count(retrieved_context)
        citations = _format_citations(result.get("citations") or [], limit=max_citations)

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        stats = {
            "llm_tokens": llm_tokens,
            "retrieved_tokens": retrieved_tokens,
            "citation_count": len(citations),
            "revision_count": int(result.get("revision_count", 0) or 0),
            "latency_ms": elapsed_ms,
        }

        payload = {
            "review": draft,
            "critique": critique,
            "queries": plan,
            "stats": stats,
            "citations": citations,
            "mode": mode,
        }
        if req.include_diagnostics:
            payload["diagnostics"] = {
                "retrieval_mode": retrieval_mode,
                "retrieval_meta": retrieval_meta,
            }
        return payload
    except Exception:
        log.exception("Error generating review")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate review",
        )


@api.post("/retrieve")
def retrieve_inspector(req: RetrieveRequest):
    svc = _require_rag()
    try:
        docs, context, diagnostics = svc.hybrid_retrieve_detailed(
            query=req.query,
            top_k_final=req.top_k,
            score_threshold=req.score_threshold,
            include_graph=req.include_graph,
            retrieval_mode=req.retrieval_mode,
        )
        return {
            "query": req.query,
            "results": docs,
            "diagnostics": diagnostics,
            "context_preview": context[:5000],
        }
    except Exception:
        log.exception("Retrieval inspector failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to inspect retrieval",
        )


@api.post("/evaluate")
def evaluate_answer(req: EvaluateRequest):
    svc = _require_rag()
    try:
        context = (req.context or "").strip()
        retrieval_preview: List[Dict[str, Any]] = []
        retrieval_diag: Dict[str, Any] = {}

        if not context:
            docs, retrieved_context, diag = svc.hybrid_retrieve_detailed(
                query=req.question,
                top_k_final=8,
                score_threshold=0.0,
                include_graph=True,
                retrieval_mode="balanced",
            )
            context = retrieved_context
            retrieval_preview = docs[:6]
            retrieval_diag = diag

        metrics = _evaluate_answer(req.question, req.answer, context)
        return {
            "metrics": metrics,
            "context_used_chars": len(context),
            "retrieval_preview": retrieval_preview,
            "retrieval_diagnostics": retrieval_diag,
        }
    except Exception:
        log.exception("Answer evaluation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate answer",
        )


@api.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    svc = _require_ingestor()

    if not svc.vs.available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store is unavailable",
        )

    filename = file.filename or "uploaded.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    content = await file.read()
    max_size = max(1, settings.MAX_UPLOAD_SIZE_MB) * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size is {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    pdf_pages = 0
    try:
        reader = PdfReader(io.BytesIO(content))
        pdf_pages = len(reader.pages)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unreadable PDF file",
        )

    try:
        metadata = svc.ingest_pdf_bytes(content, filename)
        metadata["pages"] = pdf_pages
        metadata["bytes"] = len(content)
        return {"status": "indexed", **metadata}
    except Exception:
        log.exception("Error uploading PDF")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload PDF",
        )


@api.post("/admin/clear_vector_db", dependencies=[Depends(_admin_guard)])
def clear_vector_db():
    svc = _require_ingestor()

    if not svc.vs.available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store is unavailable",
        )

    try:
        svc.vs.clear_collection()
        if migration_service is not None:
            migration_service.logs.append(
                {
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "level": "warning",
                    "message": "Vector collection cleared by admin request",
                }
            )
        return {"status": "cleared"}
    except Exception:
        log.exception("Error clearing vector DB")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear vector DB",
        )


@api.get("/admin/migration_status", dependencies=[Depends(_admin_guard)])
def migration_status():
    if migration_service is None:
        return {
            "running": False,
            "finished": False,
            "migrated": 0,
            "errors": 0,
            "uptime": "N/A",
            "message": "Migration service not initialized",
        }

    return {
        "running": migration_service.running,
        "finished": migration_service.finished,
        "migrated": migration_service.migrated,
        "errors": migration_service.errors,
        "uptime": migration_service.uptime,
    }


@api.post("/admin/restart_migration", dependencies=[Depends(_admin_guard)])
def restart_migration():
    if migration_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Migration service not initialized",
        )

    try:
        migration_service.start_background_migration()
        return {"status": "restarted"}
    except Exception:
        log.exception("Error restarting migration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restart migration",
        )


@api.get("/admin/stats", dependencies=[Depends(_admin_guard)])
def corpus_stats():
    if ingestor is None:
        return {
            "documents": 0,
            "passages": 0,
            "embeddings": 0,
            "message": "Ingest service not initialized",
        }

    try:
        return ingestor.get_corpus_stats()
    except Exception:
        log.exception("Failed to compute corpus stats")
        return {
            "documents": 0,
            "passages": 0,
            "embeddings": 0,
            "message": "Failed to compute stats",
        }


@api.get("/admin/logs", dependencies=[Depends(_admin_guard)])
def admin_logs():
    if migration_service is None:
        return {"logs": [], "message": "Migration service not initialized"}
    return {"logs": migration_service.logs[-100:]}


@api.get("/admin/system_info", dependencies=[Depends(_admin_guard)])
def system_info():
    embedding_name = (
        "hashed-fallback"
        if settings.EMBEDDING_STRATEGY.lower() == "hashed"
        else settings.EMBEDDING_MODEL
    )
    return {
        "version": settings.APP_VERSION,
        "vector_db": "Qdrant",
        "embedding_model": embedding_name,
        "collection": settings.COLLECTION_NAME,
        "ingestor_ready": bool(ingestor and ingestor.vs.available),
        "migration_ready": migration_service is not None,
        "rag_ready": rag_service is not None,
    }


@api.get("/admin/debug", dependencies=[Depends(_admin_guard)])
def debug_info():
    if not settings.ENABLE_DEBUG_ENDPOINT:
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "startup_error": startup_error,
        "ingestor_initialized": ingestor is not None,
        "vector_store_available": bool(ingestor and ingestor.vs.available),
        "migration_service_initialized": migration_service is not None,
        "rag_service_initialized": rag_service is not None,
        "python_version": sys.version,
    }


@api.get("/admin/collection_info", dependencies=[Depends(_admin_guard)])
def collection_info():
    svc = ingestor
    if svc is None:
        svc = IngestService()

    if not svc.vs.available:
        raise HTTPException(status_code=503, detail="Vector store unavailable")

    try:
        total_vectors = svc.vs.count_points()
        return {
            "collection_name": settings.COLLECTION_NAME,
            "total_vectors": total_vectors,
        }
    except Exception:
        log.exception("Failed to fetch collection info")
        raise HTTPException(status_code=500, detail="Qdrant error")


@api.post("/test/retrieval_only")
def test_retrieval(req: Request):
    svc = _require_ingestor()
    if not svc.vs.available:
        raise HTTPException(status_code=503, detail="Vector store not available")

    start = time.time()
    try:
        results = svc.vs.search(req.topic, top_k=5)
        elapsed = time.time() - start

        return {
            "query": req.topic,
            "retrieval_time_ms": int(elapsed * 1000),
            "num_results": len(results),
        }
    except Exception:
        log.exception("Retrieval benchmark failed")
        raise HTTPException(status_code=500, detail="Retrieval benchmark failed")


@api.get("/admin/paper_count", dependencies=[Depends(_admin_guard)])
def paper_count():
    svc = ingestor
    if svc is None:
        svc = IngestService()

    if not svc.vs.available:
        raise HTTPException(status_code=503, detail="Vector store unavailable")

    try:
        points = svc.vs.iter_points(limit=10_000)
        unique_papers = {
            (pt.payload or {}).get("paper_id")
            for pt in points
            if (pt.payload or {}).get("paper_id")
        }
        return {
            "unique_papers": len(unique_papers),
            "total_chunks_sampled": len(points),
        }
    except Exception:
        log.exception("Failed to estimate paper count")
        raise HTTPException(status_code=500, detail="Qdrant error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:api",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
