from __future__ import annotations

from typing import Any, Dict, List, Tuple

from src.config import settings
from src.db.graph_store import GraphStore
from src.db.vector_store import VectorStore
from src.logger import get_logger

log = get_logger("RAGService")


class RAGService:
    def __init__(self):
        self.vs = VectorStore()
        self.gs = GraphStore()

    @staticmethod
    def _as_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except Exception:
            return default

    @staticmethod
    def _trim_text(text: Any, max_chars: int) -> str:
        cleaned = str(text or "").strip()
        if len(cleaned) <= max_chars:
            return cleaned
        return cleaned[: max(0, max_chars - 1)].rstrip() + "…"

    def _normalize_vector_hit(self, hit: Any) -> Dict[str, Any] | None:
        payload = getattr(hit, "payload", None) or {}
        paper_id = str(payload.get("paper_id") or "").strip()
        text = str(payload.get("text") or "").strip()
        if not paper_id or not text:
            return None

        title = str(payload.get("title") or "Untitled").strip()
        chunk_index = int(payload.get("chunk_index") or 0)
        score = self._as_float(getattr(hit, "score", 0.0), 0.0)
        return {
            "paper_id": paper_id,
            "title": title,
            "text": text,
            "chunk_index": chunk_index,
            "source": "Vector",
            "score": score,
        }

    def _graph_doc_from_payload(self, payload: Dict[str, Any], score: float) -> Dict[str, Any] | None:
        paper_id = str(payload.get("paper_id") or "").strip()
        text = str(payload.get("text") or payload.get("abstract") or "").strip()
        if not paper_id or not text:
            return None

        return {
            "paper_id": paper_id,
            "title": str(payload.get("title") or "Untitled").strip(),
            "text": text,
            "chunk_index": int(payload.get("chunk_index") or 0),
            "source": "Graph",
            "score": max(0.0, score),
        }

    @staticmethod
    def _doc_key(doc: Dict[str, Any]) -> Tuple[str, int, str]:
        paper_id = str(doc.get("paper_id") or "")
        chunk_index = int(doc.get("chunk_index") or 0)
        text_head = str(doc.get("text") or "")[:120]
        return paper_id, chunk_index, text_head

    def _dedupe_and_rank(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deduped: Dict[Tuple[str, int, str], Dict[str, Any]] = {}
        for doc in docs:
            key = self._doc_key(doc)
            existing = deduped.get(key)
            if existing is None or self._as_float(doc.get("score")) > self._as_float(existing.get("score")):
                deduped[key] = doc

        ranked = sorted(
            deduped.values(),
            key=lambda d: self._as_float(d.get("score")),
            reverse=True,
        )
        return ranked

    def _build_context(self, docs: List[Dict[str, Any]], max_chars: int) -> str:
        blocks: List[str] = []
        total = 0
        for i, d in enumerate(docs, start=1):
            block = (
                f"[{i}] {d.get('source', 'Vector')} | score={self._as_float(d.get('score')):.3f} | "
                f"{d.get('title', 'Untitled')}\n{d.get('text', '')}"
            )
            if total + len(block) > max_chars:
                break
            blocks.append(block)
            total += len(block) + 2
        return "\n\n".join(blocks)

    def hybrid_retrieve(
        self,
        query: str,
        top_k_final: int | None = None,
        score_threshold: float = 0.0,
        include_graph: bool = True,
        retrieval_mode: str = "balanced",
    ) -> Tuple[List[Dict[str, Any]], str]:
        docs, context, _ = self.hybrid_retrieve_detailed(
            query=query,
            top_k_final=top_k_final,
            score_threshold=score_threshold,
            include_graph=include_graph,
            retrieval_mode=retrieval_mode,
        )
        return docs, context

    def hybrid_retrieve_detailed(
        self,
        query: str,
        top_k_final: int | None = None,
        score_threshold: float = 0.0,
        include_graph: bool = True,
        retrieval_mode: str = "balanced",
    ) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
        if not self.vs.available:
            return [], "", {"error": "Vector store unavailable"}

        query = (query or "").strip()
        if not query:
            return [], "", {"error": "Query is empty"}

        mode = (retrieval_mode or "balanced").strip().lower()
        if mode not in {"focused", "balanced", "broad"}:
            mode = "balanced"

        top_k_final = max(1, int(top_k_final or settings.TOP_K_FINAL))
        score_threshold = max(0.0, float(score_threshold or 0.0))

        mode_multiplier = {"focused": 1.0, "balanced": 1.4, "broad": 2.0}[mode]
        vector_limit = max(settings.TOP_K_VECTOR, int(top_k_final * mode_multiplier) + 2)
        graph_limit = max(settings.TOP_K_GRAPH, int(top_k_final * 0.8))

        vector_hits = self.vs.search(query, vector_limit)
        vector_docs: List[Dict[str, Any]] = []
        dropped_by_threshold = 0
        for hit in vector_hits:
            doc = self._normalize_vector_hit(hit)
            if doc is None:
                continue
            if self._as_float(doc.get("score")) < score_threshold:
                dropped_by_threshold += 1
                continue
            vector_docs.append(doc)

        graph_docs: List[Dict[str, Any]] = []
        if include_graph and vector_docs:
            paper_ids = list({str(d.get("paper_id")) for d in vector_docs if d.get("paper_id")})
            related_ids = self.gs.related_by_authors(paper_ids, limit=graph_limit)
            max_vec_score = max((self._as_float(d.get("score")) for d in vector_docs), default=0.35)
            graph_seed_score = max(0.08, max_vec_score * 0.78)
            for idx, pid in enumerate(related_ids):
                payload = self.vs.get_by_id(pid)
                if not payload:
                    continue
                doc = self._graph_doc_from_payload(payload, score=graph_seed_score - (idx * 0.015))
                if doc is None:
                    continue
                if self._as_float(doc.get("score")) < score_threshold:
                    dropped_by_threshold += 1
                    continue
                graph_docs.append(doc)

        ranked_docs = self._dedupe_and_rank(vector_docs + graph_docs)

        if mode == "focused":
            keep_count = top_k_final
            max_doc_chars = 820
            max_context_chars = 10_000
        elif mode == "broad":
            keep_count = min(30, max(top_k_final * 2, top_k_final + 4))
            max_doc_chars = 1_350
            max_context_chars = 15_000
        else:
            keep_count = min(24, max(top_k_final + 2, top_k_final))
            max_doc_chars = 1_050
            max_context_chars = 12_000

        selected: List[Dict[str, Any]] = []
        for rank, doc in enumerate(ranked_docs[:keep_count], start=1):
            text = self._trim_text(doc.get("text", ""), max_doc_chars)
            selected.append(
                {
                    **doc,
                    "rank": rank,
                    "text": text,
                    "snippet": self._trim_text(text.replace("\n", " "), 260),
                }
            )

        context = self._build_context(selected, max_chars=max_context_chars)
        selected_scores = [self._as_float(d.get("score")) for d in selected]
        diagnostics = {
            "query": query,
            "mode": mode,
            "score_threshold": score_threshold,
            "vector_hits_before_filter": len(vector_hits),
            "vector_hits_after_filter": len(vector_docs),
            "graph_hits_after_filter": len(graph_docs),
            "dropped_by_threshold": dropped_by_threshold,
            "returned_docs": len(selected),
            "score_min": min(selected_scores) if selected_scores else 0.0,
            "score_max": max(selected_scores) if selected_scores else 0.0,
        }
        return selected, context, diagnostics
