# src/services/ingest_service.py

import uuid

from src.utils.pdf import extract_pdf_text
from src.utils.chunking import chunk_text
from src.db.graph_store import GraphStore
from src.db.vector_store import VectorStore
from src.logger import get_logger

log = get_logger("IngestService")


class IngestService:
    def __init__(self):
        self.vs = VectorStore()
        self.gs = GraphStore()
        self.documents_count = 0
        self.passages_count = 0
        self.embeddings_count = 0
        if not self.vs.available:
            log.warning("IngestService initialized but VectorStore is unavailable")

    def ingest_pdf_bytes(self, pdf_bytes: bytes, filename: str):
        text = extract_pdf_text(pdf_bytes)
        title = filename.replace(".pdf", "")
        paper_id = str(uuid.uuid4())[:8]
        meta = self.ingest_text(
            paper_id=paper_id,
            title=title,
            text=text,
            source="Upload",
            authors=["Uploaded User"],
        )
        meta["text_chars"] = len(text or "")
        return meta

    def ingest_text(
        self,
        paper_id: str,
        title: str,
        text: str,
        source: str = "Upload",
        authors: list[str] | None = None,
    ):
        if not self.vs.available:
            raise RuntimeError("Vector store is unavailable")

        authors = authors or ["Unknown"]
        log.info(
            "Ingesting text: title=%s, paper_id=%s, text_len=%d",
            title,
            paper_id,
            len(text or ""),
        )

        chunks = chunk_text(text or "")
        if not chunks:
            log.warning("No chunks produced for %s (paper_id=%s)", title, paper_id)

        for i, ch in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            self.vs.upsert_chunk(
                chunk_id=chunk_id,
                text=ch,
                payload={
                    "paper_id": paper_id,
                    "title": title,
                    "chunk_index": i,
                    "source": source,
                },
            )

        try:
            self.gs.add_paper(paper_id=paper_id, title=title, authors=authors)
        except Exception as e:
            log.warning("Graph update skipped for paper %s: %s", paper_id, e)

        self.documents_count += 1
        self.passages_count += len(chunks)
        self.embeddings_count += len(chunks)
        return {"paper_id": paper_id, "title": title, "chunks": len(chunks)}

    def get_corpus_stats(self):
        if not self.vs.available:
            return {"documents": 0, "passages": 0, "embeddings": 0}

        points = self.vs.iter_points(limit=10_000)
        paper_ids = {
            (pt.payload or {}).get("paper_id")
            for pt in points
            if (pt.payload or {}).get("paper_id")
        }
        passages = len(points)
        return {
            "documents": len(paper_ids),
            "passages": passages,
            "embeddings": passages,
        }
