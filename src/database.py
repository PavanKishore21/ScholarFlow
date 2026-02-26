"""
Backward-compatible facade over the current storage/services layer.

This keeps older scripts working while the app uses src/services/* directly.
"""

import tempfile
import uuid

from src.services.ingest_service import IngestService
from src.services.rag_service import RAGService
from src.db.graph_store import GraphStore


class Database:
    def __init__(self):
        self.ingestor = IngestService()
        self.rag = RAGService()
        self.graph = GraphStore()

    def close(self):
        # JSON graph + Qdrant HTTP client do not require explicit teardown.
        return None

    def initialize_indexes(self):
        # Collection initialization is handled by VectorStore on construction.
        return True

    def add_paper(self, arxiv_id, title, abstract, authors, source="arXiv"):
        self.ingestor.ingest_text(
            paper_id=arxiv_id or str(uuid.uuid4())[:8],
            title=title,
            text=f"{title}\n\n{abstract}",
            source=source,
            authors=authors or ["Unknown"],
        )
        return True

    def hybrid_search(self, query, top_k=5):
        docs, _ = self.rag.hybrid_retrieve(query)
        if not docs:
            return ""

        lines = []
        for doc in docs[:top_k]:
            lines.append(
                f"[Source: {doc.get('source', 'Vector')}] "
                f"Title: {doc.get('title', 'Untitled')}\n"
                f"Abstract: {doc.get('text', '')}"
            )
        return "\n\n".join(lines)

    def visualize_graph(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w+") as tmp:
            self.graph.to_pyvis(outfile=tmp.name)
            return tmp.name
