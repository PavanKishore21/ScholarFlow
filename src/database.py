from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from src.config import *
import uuid
import networkx as nx
from pyvis.network import Network
import tempfile

class Database:
    def __init__(self):
        print(f"🔌 Connecting to Qdrant & Neo4j...")
        self.vector_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        self.graph_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        self.encoder = SentenceTransformer(EMBEDDING_MODEL)

    def close(self):
        self.graph_driver.close()

    def initialize_indexes(self):
        if not self.vector_client.collection_exists(COLLECTION_NAME):
            self.vector_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
        with self.graph_driver.session() as session:
            session.run("CREATE CONSTRAINT paper_id IF NOT EXISTS FOR (p:Paper) REQUIRE p.id IS UNIQUE")

    def add_paper(self, arxiv_id, title, abstract, authors, source="arXiv"):
        # 1. Vector Store
        text_content = f"{title} {abstract}"
        embedding = self.encoder.encode(text_content).tolist()
        
        self.vector_client.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={"id": arxiv_id, "title": title, "abstract": abstract, "source": source}
            )]
        )
        # 2. Graph Store
        with self.graph_driver.session() as session:
            session.run("""
                MERGE (p:Paper {id: $id})
                SET p.title = $title, p.abstract = $abstract, p.source = $source
                FOREACH (a IN $authors | 
                    MERGE (auth:Author {name: a})
                    MERGE (p)-[:AUTHORED_BY]->(auth)
                )
            """, id=arxiv_id, title=title, abstract=abstract, authors=authors, source=source)

    def hybrid_search(self, query, top_k=5):
        query_vec = self.encoder.encode(query).tolist()
        try:
            vec_results = self.vector_client.query_points(
                collection_name=COLLECTION_NAME, query=query_vec, limit=top_k
            ).points
        except:
            return ""
        
        if not vec_results: return ""

        paper_ids = [r.payload['id'] for r in vec_results]
        
        graph_docs = []
        if paper_ids:
            with self.graph_driver.session() as session:
                graph_results = session.run("""
                    MATCH (p:Paper)-[:AUTHORED_BY]->(a:Author)<-[:AUTHORED_BY]-(related:Paper)
                    WHERE p.id IN $ids AND p <> related
                    RETURN related.title as title, related.abstract as abstract
                    LIMIT 3
                """, ids=paper_ids)
                graph_docs = [{"title": r["title"], "abstract": r["abstract"], "source": "Graph"} for r in graph_results]

        vector_docs = [{"title": r.payload['title'], "abstract": r.payload['abstract'], "source": "Vector"} for r in vec_results]
        
        context = []
        for doc in vector_docs + graph_docs:
            context.append(f"[Source: {doc['source']}] Title: {doc['title']}\nAbstract: {doc['abstract']}")
            
        return "\n\n".join(context)

    # --- NEW FEATURE: GRAPH VISUALIZATION ---
    def visualize_graph(self):
        """Generates an HTML file for the knowledge graph."""
        net = Network(height="600px", width="100%", bgcolor="#1e293b", font_color="white")
        
        with self.graph_driver.session() as session:
            # Fetch a subgraph (limit to 50 nodes for performance)
            result = session.run("""
                MATCH (p:Paper)-[r:AUTHORED_BY]->(a:Author)
                RETURN p.title as paper, a.name as author
                LIMIT 50
            """)
            
            for record in result:
                # Truncate long titles
                title = (record['paper'][:20] + '..') if len(record['paper']) > 20 else record['paper']
                net.add_node(record['paper'], label=title, color="#6366f1", title=record['paper']) # Paper Node
                net.add_node(record['author'], label=record['author'], color="#10b981", shape="ellipse") # Author Node
                net.add_edge(record['paper'], record['author'], color="#94a3b8")

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode='w+') as tmp:
            net.save_graph(tmp.name)
            return tmp.name