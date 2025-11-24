from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter
from src.config import settings
from src.db.embeddings import get_encoder
from src.logger import get_logger
import uuid

log = get_logger("VectorStore")

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        self.encoder = get_encoder()
        self.init_collection()

    def init_collection(self):
        if not self.client.collection_exists(settings.COLLECTION_NAME):
            log.info("Creating Qdrant collection...")
            self.client.create_collection(
                collection_name=settings.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=settings.VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )

    # -------------------------
    # ✅ CLEAR VECTOR DB
    # -------------------------
    def clear_collection(self):
        log.warning("Clearing Qdrant collection...")
        self.client.delete_collection(settings.COLLECTION_NAME)
        self.init_collection()
        return True

   

    # -------------------------
    # UPSERT
    # -------------------------
    def upsert_chunk(self, chunk_id: str, text: str, payload: dict):
        vec = self.encoder.encode(text).tolist()

        # enforce schema fields
        payload = {
            "schema_version": settings.PAYLOAD_SCHEMA_VERSION,
            **payload,
            "text": text
        }

        self.client.upsert(
            collection_name=settings.COLLECTION_NAME,
            points=[
                PointStruct(id=chunk_id, vector=vec, payload=payload)
            ]
        )

    # -------------------------
    # SEARCH
    # -------------------------
    def search(self, query: str, top_k: int):
        qv = self.encoder.encode(query).tolist()
        res = self.client.query_points(
            collection_name=settings.COLLECTION_NAME,
            query=qv,
            limit=top_k,
            with_payload=True
        ).points
        return res
