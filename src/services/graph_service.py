import tempfile
from src.db.graph_store import GraphStore

class GraphService:
    def __init__(self):
        self.gs = GraphStore()

    def visualize_subgraph(self, limit=80):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w+") as tmp:
            out = self.gs.to_pyvis(outfile=tmp.name)
            with open(out, "r", encoding="utf-8") as f:
                return f.read()
