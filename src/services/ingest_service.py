import uuid
from src.utils.pdf import extract_pdf_text
from src.utils.chunking import chunk_text
from src.db.vector_store import VectorStore
from src.db.graph_store import GraphStore

class IngestService:
    def __init__(self):
        self.vs = VectorStore()
        self.gs = GraphStore()
        self.vs.init_collection()
        self.gs = GraphStore()


    def ingest_pdf_bytes(self, pdf_bytes: bytes, filename: str):
        text = extract_pdf_text(pdf_bytes)

        title = filename.replace(".pdf", "")
        abstract = (text[:1200].strip() + "...") if text else "No text extracted."

        paper_id = str(uuid.uuid4())[:8]
        authors = ["Uploaded User"]

        # Graph store
        self.gs.add_paper(paper_id, title, abstract, authors, "Upload")

        # Vector store (chunks)
        chunks = chunk_text(text)
        for i, ch in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            self.vs.upsert_chunk(
                chunk_id=chunk_id,
                text=ch,
                payload={
                    "paper_id": paper_id,
                    "title": title,
                    "chunk_index": i,
                    "source": "Upload"
                }
            )


        return {"paper_id": paper_id, "title": title, "chunks": len(chunks)}
