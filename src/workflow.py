from __future__ import annotations

from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph

from src.agents.research_agents import ResearchAgents


class AgentState(TypedDict, total=False):
    task: str
    mode: str
    max_plan_queries: int
    max_citations: int
    score_threshold: float
    include_graph: bool
    plan: List[str]
    context: str
    draft: str
    critique: str
    citations: List[dict]
    retrieval_meta: Dict[str, Any]
    revision_count: int


agents = ResearchAgents()


def planner_node(state: AgentState):
    max_queries = int(state.get("max_plan_queries", 3) or 3)
    return {"plan": agents.plan(state.get("task", ""), max_queries=max_queries)}


def researcher_node(state: AgentState):
    context, citations, retrieval_meta = agents.retrieve(
        queries=state.get("plan", []),
        retrieval_mode=state.get("mode", "balanced"),
        top_k_final=int(state.get("max_citations", 8) or 8),
        score_threshold=float(state.get("score_threshold", 0.0) or 0.0),
        include_graph=bool(state.get("include_graph", True)),
    )
    return {
        "context": context,
        "citations": citations,
        "retrieval_meta": retrieval_meta,
    }


def writer_node(state: AgentState):
    return {
        "draft": agents.draft(
            task=state.get("task", ""),
            context=state.get("context", ""),
            citations=state.get("citations", []),
            mode=state.get("mode", "balanced"),
        ),
        "revision_count": int(state.get("revision_count", 0) or 0) + 1,
    }


def critic_node(state: AgentState):
    return {"critique": agents.critique(state.get("draft", ""))}


def should_continue(state: AgentState):
    critique_text = str(state.get("critique") or "").upper()
    if "REVISE" in critique_text and int(state.get("revision_count", 0) or 0) < 2:
        return "Writer"
    return END


graph = StateGraph(AgentState)
graph.add_node("Planner", planner_node)
graph.add_node("Researcher", researcher_node)
graph.add_node("Writer", writer_node)
graph.add_node("Critic", critic_node)

graph.set_entry_point("Planner")
graph.add_edge("Planner", "Researcher")
graph.add_edge("Researcher", "Writer")
graph.add_edge("Writer", "Critic")
graph.add_conditional_edges("Critic", should_continue, {"Writer": "Writer", END: END})

app = graph.compile()
