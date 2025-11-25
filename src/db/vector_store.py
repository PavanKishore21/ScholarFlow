# src/db/vector_store.py

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from src.config import settings
from src.db.embeddings import get_encoder
from src.logger import get_logger

log = get_logger("VectorStore")


def _to_list(vec):
    """Normalize encoder output to a plain Python list[float]."""
    if vec is None:
        return []
    # torch / numpy / etc.
    if hasattr(vec, "tolist"):
        return vec.tolist()
    # already a list or other iterable
    try:
        return list(vec)
    except TypeError:
        # last resort – single scalar
        return [float(vec)]


class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
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
                    distance=Distance.COSINE,
                ),
            )
        else:
            log.info("✅ VectorStore initialized")

    # -------------------------
    # CLEAR
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
        raw_vec = self.encoder.encode(text)
        vec = _to_list(raw_vec)

        payload = {
            "schema_version": settings.PAYLOAD_SCHEMA_VERSION,
            **payload,
            "text": text,
        }

        self.client.upsert(
            collection_name=settings.COLLECTION_NAME,
            points=[PointStruct(id=chunk_id, vector=vec, payload=payload)],
        )

    # -------------------------
    # SEARCH
    # -------------------------
    def search(self, query: str, top_k: int):
        raw_qv = self.encoder.encode(query)
        qv = _to_list(raw_qv)

        res = self.client.query_points(
            collection_name=settings.COLLECTION_NAME,
            query=qv,
            limit=top_k,
            with_payload=True,
        ).points
        return res
