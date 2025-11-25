# src/db/vector_store.py

import uuid
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse, ApiException

from src.config import settings
from src.db.embeddings import get_encoder
from src.logger import get_logger

log = get_logger("VectorStore")


class VectorStore:
    def __init__(self) -> None:
        """
        Initialize Qdrant client and encoder.

        This is made robust for cloud:
        - If Qdrant is unreachable or misconfigured, we don't crash the app.
        - Instead, we set `available = False` and log the error.
        """
        self.client: QdrantClient | None = None
        self.encoder = None
        self.available: bool = False

        try:
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
            )
            self.encoder = get_encoder()
            self._init_collection()
            self.available = True
            log.info("✅ VectorStore initialized and collection ready")
        except Exception as e:
            log.exception(f"❌ Failed to initialize VectorStore: {e}")
            self.client = None
            self.encoder = None
            self.available = False

    # -------------------------
    # INTERNAL: ensure collection
    # -------------------------
    def _init_collection(self) -> None:
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

    def _ensure_available(self) -> None:
        if not self.available or self.client is None or self.encoder is None:
            raise RuntimeError("VectorStore is not available (Qdrant/encoder failed to initialize)")

    # -------------------------
    # ✅ CLEAR VECTOR DB
    # -------------------------
    def clear_collection(self) -> bool:
        if not self.available or self.client is None:
            log.warning("clear_collection called but VectorStore is unavailable")
            return False

        log.warning("Clearing Qdrant collection '%s'...", settings.COLLECTION_NAME)
        try:
            self.client.delete_collection(settings.COLLECTION_NAME)
        except (ApiException, UnexpectedResponse) as e:
            log.exception(f"Error deleting Qdrant collection: {e}")

        # Recreate it
        self._init_collection()
        return True

    # -------------------------
    # UPSERT
    # -------------------------
    def upsert_chunk(self, chunk_id: str, text: str, payload: dict) -> None:
        self._ensure_available()

        vec = self.encoder.encode(text).tolist()  # type: ignore[union-attr]

        # enforce schema fields
        full_payload = {
            "schema_version": settings.PAYLOAD_SCHEMA_VERSION,
            **payload,
            "text": text,
        }

        self.client.upsert(  # type: ignore[union-attr]
            collection_name=settings.COLLECTION_NAME,
            points=[
                PointStruct(id=chunk_id, vector=vec, payload=full_payload),
            ],
        )

    # -------------------------
    # SEARCH
    # -------------------------
    def search(self, query: str, top_k: int) -> List:
        """
        Return a list of Qdrant ScoredPoint.
        If the store is not available, return an empty list instead of crashing.
        """
        if not self.available or self.client is None or self.encoder is None:
            log.warning("search called but VectorStore is unavailable; returning empty list")
            return []

        qv = self.encoder.encode(query).tolist()
        res = self.client.query_points(
            collection_name=settings.COLLECTION_NAME,
            query=qv,
            limit=top_k,
            with_payload=True,
        ).points
        return res
