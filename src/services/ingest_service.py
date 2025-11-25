# src/services/ingest_service.py

import uuid

from src.utils.pdf import extract_pdf_text
from src.utils.chunking import chunk_text
from src.db.vector_store import VectorStore
from src.logger import get_logger

log = get_logger("IngestService")


class IngestService:
    def __init__(self):
        self.vs = VectorStore()
        if not self.vs.available:
            log.warning("IngestService initialized but VectorStore is unavailable")

    def ingest_pdf_bytes(self, pdf_bytes: bytes, filename: str):
        text = extract_pdf_text(pdf_bytes)
        title = filename.replace(".pdf", "")
        abstract = (text[:1200].strip() + "...") if text else "No text extracted."

        paper_id = str(uuid.uuid4())[:8]
        authors = ["Uploaded User"]  # keep placeholder for future graph

        log.info(
            "Ingesting PDF: title=%s, paper_id=%s, text_len=%d",
            title,
            paper_id,
            len(text or ""),
        )

        chunks = chunk_text(text or "")
        if not chunks:
            log.warning("No chunks produced for %s (paper_id=%s)", title, paper_id)

        for i, ch in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            try:
                self.vs.upsert_chunk(
                    chunk_id=chunk_id,
                    text=ch,
                    payload={
                        "paper_id": paper_id,
                        "title": title,
                        "chunk_index": i,
                        "source": "Upload",
                    },
                )
            except Exception as e:
                log.exception(f"Failed to upsert chunk {chunk_id} for paper {paper_id}: {e}")

        return {"paper_id": paper_id, "title": title, "chunks": len(chunks)}
