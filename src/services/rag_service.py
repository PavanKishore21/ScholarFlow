from src.config import settings
from src.db.vector_store import VectorStore
from src.db.graph_store import GraphStore

class RAGService:
    def __init__(self):
        self.vs = VectorStore()
        self.gs = GraphStore()

    def hybrid_retrieve(self, query: str):
        vec_hits = self.vs.search(query, settings.TOP_K_VECTOR)

        # filter out broken payloads (just in case)
        vec_hits = [
            h for h in vec_hits
            if h.payload and h.payload.get("paper_id") and h.payload.get("text")
        ]

        if not vec_hits:
            return [], ""

        paper_ids = list({h.payload["paper_id"] for h in vec_hits})
        graph_related_ids = self.gs.related_by_authors(paper_ids, limit=settings.TOP_K_GRAPH)

        graph_hits = []
        for pid in graph_related_ids:
            # get metadata from Qdrant
            result = self.vs.get_by_id(pid)
            if result:
                graph_hits.append(result)


        vector_docs = [{
            "title": h.payload["title"],
            "text": h.payload["text"],
            "paper_id": h.payload["paper_id"],
            "source": "Vector"
        } for h in vec_hits]

        graph_docs = [{
            "title": g["title"],
            "text": g["abstract"],
            "paper_id": g["id"],
            "source": "Graph"
        } for g in graph_hits]

        docs = vector_docs + graph_docs

        context = "\n\n".join(
            f"[{d['source']}] {d['title']}\n{d['text']}"
            for d in docs
        )

        return docs[:settings.TOP_K_FINAL], context[:9000]
