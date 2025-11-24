from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from src.config import settings
from src.services.rag_service import RAGService

class ResearchAgents:
    def __init__(self):
        self.planner = ChatGroq(model=settings.LLM_FAST, api_key=settings.GROQ_API_KEY)
        self.writer  = ChatGroq(model=settings.LLM_SMART, api_key=settings.GROQ_API_KEY)
        self.rag = RAGService()

    def plan(self, task: str):
        prompt = (
            "Return a python list of 3 diverse search queries "
            f"to research this topic: '{task}'. Return ONLY the list."
        )
        res = self.planner.invoke([HumanMessage(content=prompt)])
        try:
            return eval(res.content)
        except:
            return [task]

    def retrieve(self, queries: list):
        context = ""
        for q in queries:
            _, ctx = self.rag.hybrid_retrieve(q)
            context += ctx + "\n"
        return context[:9000]

    def draft(self, task: str, context: str):
        prompt = f"""
Write a comprehensive literature review on: {task}

Use the retrieved context below. Cite sources inline like [Vector] / [Graph].

CONTEXT:
{context}

Return Markdown only.
"""
        return self.writer.invoke([HumanMessage(content=prompt)]).content

    def critique(self, draft: str):
        prompt = f"""
Act as a strict academic reviewer.
If good reply exactly: APPROVE
Else reply: REVISE: <bulleted fixes>

DRAFT:
{draft[:2500]}
"""
        return self.planner.invoke([HumanMessage(content=prompt)]).content
