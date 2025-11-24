from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from src.agents.research_agents import ResearchAgents

class AgentState(TypedDict):
    task: str
    plan: List[str]
    context: str
    draft: str
    critique: str
    revision_count: int

agents = ResearchAgents()

def planner_node(state: AgentState):
    return {"plan": agents.plan(state["task"])}

def researcher_node(state: AgentState):
    return {"context": agents.retrieve(state["plan"])}

def writer_node(state: AgentState):
    return {
        "draft": agents.draft(state["task"], state["context"]),
        "revision_count": state.get("revision_count", 0) + 1
    }

def critic_node(state: AgentState):
    return {"critique": agents.critique(state["draft"])}

def should_continue(state: AgentState):
    if "REVISE" in state["critique"] and state["revision_count"] < 2:
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
