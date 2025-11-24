import json
import os
from pathlib import Path
from src.logger import get_logger

log = get_logger("GraphStore")

GRAPH_FILE = Path("data/graph.json")


class GraphStore:
    def __init__(self):
        self.graph = {"nodes": [], "edges": []}
        self._load()

    def _load(self):
        if GRAPH_FILE.exists():
            try:
                with open(GRAPH_FILE, "r") as f:
                    self.graph = json.load(f)
                log.info("Graph loaded.")
            except Exception as e:
                log.error(f"Failed to load graph: {e}")

    def _save(self):
        GRAPH_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(GRAPH_FILE, "w") as f:
            json.dump(self.graph, f, indent=2)
        log.info("Graph saved.")

    # ------------------------------------------------------------
    # BASIC OPERATIONS
    # ------------------------------------------------------------
    def add_paper(self, paper_id: str, title: str, authors: list):
        """Adds paper + edges to authors."""
        # Add paper node
        self.graph["nodes"].append({
            "id": paper_id,
            "type": "paper",
            "title": title,
            "authors": authors
        })

        # Add author nodes + edges
        for a in authors:
            self.graph["nodes"].append({
                "id": f"author:{a}",
                "type": "author",
                "name": a
            })
            self.graph["edges"].append({
                "source": paper_id,
                "target": f"author:{a}",
                "type": "AUTHORED_BY"
            })

        self._save()

    # ------------------------------------------------------------
    # NEW — "related_by_authors" for JSON graph
    # ------------------------------------------------------------
    def related_by_authors(self, paper_ids, limit=5):
        """
        Return papers that share authors with any of the given paper IDs.
        Works with the new JSON-based graph structure.
        """
        related = []

        for edge in self.graph["edges"]:
            if edge["type"] != "AUTHORED_BY":
                continue

            # Example: source = paperID, target = author:<name>
            if edge["source"] in paper_ids:
                author_node = edge["target"]

                # find all papers connected to same author
                for e2 in self.graph["edges"]:
                    if (
                        e2["target"] == author_node
                        and e2["source"] not in paper_ids
                    ):
                        related.append(e2["source"])

        # Deduplicate and limit
        related = list(dict.fromkeys(related))[:limit]

        return related

    # ------------------------------------------------------------
    # For visualization
    # ------------------------------------------------------------
    def to_pyvis(self, outfile="graph_vis.html"):
        from pyvis.network import Network

        net = Network(height="600px", width="100%", bgcolor="#111", font_color="white")

        for node in self.graph["nodes"]:
            if node["type"] == "paper":
                net.add_node(node["id"], label=node["title"], color="#6366f1")
            else:
                net.add_node(node["id"], label=node.get("name"), color="#10b981")

        for e in self.graph["edges"]:
            net.add_edge(e["source"], e["target"], color="#94a3b8")

        net.save_graph(outfile)
        return outfile
