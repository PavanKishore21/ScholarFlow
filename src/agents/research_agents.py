from __future__ import annotations

import ast
from typing import Any, Dict, List, Tuple

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from src.config import settings
from src.logger import get_logger
from src.services.rag_service import RAGService

log = get_logger("ResearchAgents")


class ResearchAgents:
    def __init__(self):
        self.rag = RAGService()
        self.planner: ChatGroq | None = None
        self.writer: ChatGroq | None = None

        if settings.GROQ_API_KEY:
            try:
                self.planner = ChatGroq(model=settings.LLM_FAST, api_key=settings.GROQ_API_KEY)
                self.writer = ChatGroq(model=settings.LLM_SMART, api_key=settings.GROQ_API_KEY)
            except Exception as e:
                log.warning("Failed to initialize Groq models; fallback mode enabled: %s", e)
        else:
            log.warning("GROQ_API_KEY is not configured; using fallback agent behavior.")

    @staticmethod
    def _safe_int(value: Any, default: int, min_value: int, max_value: int) -> int:
        try:
            parsed = int(value)
        except Exception:
            parsed = default
        return max(min_value, min(max_value, parsed))

    @staticmethod
    def _parse_query_list(raw: Any, max_queries: int) -> List[str]:
        text = str(raw or "").strip()
        if not text:
            return []

        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, list):
                values = [str(q).strip() for q in parsed if str(q).strip()]
                return values[:max_queries]
        except Exception:
            pass

        lines = [ln.strip("-• ").strip() for ln in text.splitlines()]
        values = [ln for ln in lines if ln]
        return values[:max_queries]

    @staticmethod
    def _fallback_queries(task: str, max_queries: int) -> List[str]:
        base = (task or "").strip()
        if not base:
            return ["retrieval augmented generation best practices"]

        templates = [
            f"{base}",
            f"{base} architecture patterns and tradeoffs",
            f"{base} evaluation metrics and benchmarking",
            f"{base} production reliability and monitoring",
            f"{base} failure modes and mitigation strategies",
        ]
        deduped: List[str] = []
        for q in templates:
            if q not in deduped:
                deduped.append(q)
            if len(deduped) >= max_queries:
                break
        return deduped or [base]

    def plan(self, task: str, max_queries: int = 3) -> List[str]:
        max_queries = self._safe_int(max_queries, default=3, min_value=1, max_value=6)
        prompt = (
            "Return a python list of concise, diverse retrieval queries. "
            "Keep each query under 14 words. "
            f"Task: '{task}'. Return ONLY the list."
        )

        if self.planner is None:
            return self._fallback_queries(task, max_queries=max_queries)

        try:
            res = self.planner.invoke([HumanMessage(content=prompt)])
            parsed = self._parse_query_list(getattr(res, "content", ""), max_queries=max_queries)
            return parsed or self._fallback_queries(task, max_queries=max_queries)
        except Exception as e:
            log.warning("Planner invocation failed; using fallback queries: %s", e)
            return self._fallback_queries(task, max_queries=max_queries)

    @staticmethod
    def _dedupe_citations(citations: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        deduped: Dict[Tuple[str, int], Dict[str, Any]] = {}
        for c in citations:
            key = (
                str(c.get("paper_id") or ""),
                int(c.get("chunk_index") or 0),
            )
            existing = deduped.get(key)
            if existing is None or float(c.get("score", 0.0) or 0.0) > float(existing.get("score", 0.0) or 0.0):
                deduped[key] = c

        ranked = sorted(
            deduped.values(),
            key=lambda d: float(d.get("score", 0.0) or 0.0),
            reverse=True,
        )
        return ranked[:limit]

    def retrieve(
        self,
        queries: List[str],
        retrieval_mode: str = "balanced",
        top_k_final: int = 6,
        score_threshold: float = 0.0,
        include_graph: bool = True,
    ) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        all_citations: List[Dict[str, Any]] = []
        per_query: List[Dict[str, Any]] = []
        context_parts: List[str] = []

        for q in queries:
            docs, context, diag = self.rag.hybrid_retrieve_detailed(
                query=q,
                top_k_final=top_k_final,
                score_threshold=score_threshold,
                include_graph=include_graph,
                retrieval_mode=retrieval_mode,
            )
            all_citations.extend(docs)
            if context:
                context_parts.append(context)
            per_query.append(
                {
                    "query": q,
                    "returned_docs": len(docs),
                    "diagnostics": diag,
                }
            )

        deduped_citations = self._dedupe_citations(all_citations, limit=max(6, top_k_final * 3))
        merged_context = "\n\n".join(context_parts)[:18_000]
        retrieval_meta = {
            "retrieval_mode": retrieval_mode,
            "query_count": len(queries),
            "per_query": per_query,
            "total_citations": len(deduped_citations),
            "score_threshold": score_threshold,
            "include_graph": include_graph,
        }
        return merged_context, deduped_citations, retrieval_meta

    @staticmethod
    def _citations_for_prompt(citations: List[Dict[str, Any]], limit: int = 12) -> str:
        lines: List[str] = []
        for idx, c in enumerate(citations[:limit], start=1):
            title = str(c.get("title") or "Untitled").strip()
            source = str(c.get("source") or "Vector").strip()
            score = float(c.get("score", 0.0) or 0.0)
            snippet = str(c.get("snippet") or c.get("text") or "").strip().replace("\n", " ")
            snippet = snippet[:220]
            lines.append(f"[{idx}] {title} ({source}, score={score:.3f}) - {snippet}")
        return "\n".join(lines)

    def _fallback_draft(self, task: str, citations: List[Dict[str, Any]]) -> str:
        bullets = []
        for idx, c in enumerate(citations[:8], start=1):
            bullets.append(
                f"- [{idx}] {c.get('title', 'Untitled')} ({c.get('source', 'Vector')}, score={float(c.get('score', 0.0) or 0.0):.3f})"
            )
        if not bullets:
            bullets = ["- No indexed evidence was retrieved. Ingest documents or reduce score threshold."]

        return (
            f"## Research Brief: {task}\n\n"
            "### Evidence Snapshot\n"
            + "\n".join(bullets)
            + "\n\n### Notes\n"
            "- The LLM writer model is unavailable, so this is an evidence-first fallback output.\n"
            "- Configure `GROQ_API_KEY` to enable full synthesis and critique.\n"
        )

    def draft(
        self,
        task: str,
        context: str,
        citations: List[Dict[str, Any]],
        mode: str = "balanced",
    ) -> str:
        evidence = self._citations_for_prompt(citations, limit=12)
        prompt = f"""
You are preparing a production-grade RAG response.

Task: {task}
Mode: {mode}

Rules:
- Ground every substantive claim in the evidence list.
- Use citation markers like [1], [2] in-line.
- If evidence is weak or missing, explicitly state uncertainty.
- Keep the structure crisp: Summary, Key Findings, Risks/Gaps, Recommended Next Steps.
- Return Markdown only.

Evidence:
{evidence}

Retrieved Context:
{context[:14000]}
"""
        if self.writer is None:
            return self._fallback_draft(task, citations)

        try:
            return str(self.writer.invoke([HumanMessage(content=prompt)]).content).strip()
        except Exception as e:
            log.warning("Writer invocation failed; using fallback draft: %s", e)
            return self._fallback_draft(task, citations)

    def critique(self, draft: str) -> str:
        prompt = f"""
Act as a strict reviewer.
If the response is acceptable and grounded, reply exactly: APPROVE
Otherwise reply: REVISE: <short bullet list of fixes>

DRAFT:
{draft[:3500]}
"""
        if self.planner is None:
            return "APPROVE"

        try:
            return str(self.planner.invoke([HumanMessage(content=prompt)]).content).strip()
        except Exception as e:
            log.warning("Critic invocation failed; defaulting to APPROVE: %s", e)
            return "APPROVE"
