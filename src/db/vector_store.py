# src/db/vector_store.py

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import ApiException, UnexpectedResponse

from src.config import settings
from src.db.embeddings import get_encoder
from src.logger import get_logger

log = get_logger("VectorStore")


class VectorStore:
    def __init__(self):
        self.client = None
        self.encoder = None
        self.available = False

        try:
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
            )
            self.encoder = get_encoder()
            self.init_collection()
            self.available = True
            log.info("✅ VectorStore initialized")
        except Exception as e:
            log.exception(f"❌ Failed to initialize VectorStore (Qdrant/encoder): {e}")
            self.client = None
            self.encoder = None
            self.available = False

    def init_collection(self):
        if self.client is None:
            raise RuntimeError("Qdrant client not initialized")

        if not self.client.collection_exists(settings.COLLECTION_NAME):
            log.info(
                "Creating Qdrant collection '%s' (dim=%d)",
                settings.COLLECTION_NAME,
                settings.VECTOR_SIZE,
            )
            self.client.create_collection(
                collection_name=settings.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=settings.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )

    def clear_collection(self):
        if not self.available or self.client is None:
            log.warning("clear_collection called but VectorStore is unavailable")
            return False

        log.warning("Clearing Qdrant collection '%s'...", settings.COLLECTION_NAME)
        try:
            self.client.delete_collection(settings.COLLECTION_NAME)
        except (ApiException, UnexpectedResponse) as e:
            log.exception(f"Error deleting Qdrant collection: {e}")

        self.init_collection()
        return True

    def upsert_chunk(self, chunk_id: str, text: str, payload: dict):
        if not self.available or self.client is None or self.encoder is None:
            log.warning("upsert_chunk called but VectorStore is unavailable; skipping")
            return

        vec = self.encoder.encode(text).tolist()
        full_payload = {
            "schema_version": settings.PAYLOAD_SCHEMA_VERSION,
            **payload,
            "text": text,
        }

        self.client.upsert(
            collection_name=settings.COLLECTION_NAME,
            points=[PointStruct(id=chunk_id, vector=vec, payload=full_payload)],
        )

    def search(self, query: str, top_k: int):
        if not self.available or self.client is None or self.encoder is None:
            log.warning("search called but VectorStore is unavailable; returning []")
            return []

        qv = self.encoder.encode(query).tolist()
        res = self.client.query_points(
            collection_name=settings.COLLECTION_NAME,
            query=qv,
            limit=top_k,
            with_payload=True,
        ).points
        return res
