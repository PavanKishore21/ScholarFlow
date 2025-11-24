import tempfile
from pyvis.network import Network
from src.db.graph_store import GraphStore

class GraphService:
    def __init__(self):
        self.gs = GraphStore()

    def visualize_subgraph(self, limit=80):
        net = Network(
            height="650px", width="100%",
            bgcolor="#111a33", font_color="white"
        )

        with self.gs.driver.session() as s:
            result = s.run("""
                MATCH (p:Paper)-[:AUTHORED_BY]->(a:Author)
                RETURN p.title as paper, a.name as author
                LIMIT $limit
            """, limit=limit)

            for r in result:
                p = r["paper"]
                a = r["author"]
                short = (p[:22] + "…") if len(p) > 22 else p

                net.add_node(p, label=short, color="#818cf8", title=p)
                net.add_node(a, label=a, color="#10b981")
                net.add_edge(p, a, color="#94a3b8")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w+") as tmp:
            net.save_graph(tmp.name)
            return open(tmp.name).read()
