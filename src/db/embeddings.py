# src/db/embeddings.py

from functools import lru_cache
import hashlib
import math
from typing import Any, List, Union

from src.config import settings
from src.logger import get_logger

log = get_logger("Embeddings")

# Try to import sentence-transformers.
# On Render backend we DO NOT install it, so this will fail and we fallback.
try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    HAS_ST = True
except Exception:
    HAS_ST = False
    SentenceTransformer = None  # type: ignore


class HashedEncoder:
    """
    Lightweight fallback encoder for environments where sentence-transformers
    is unavailable. It creates deterministic hashed vectors from token strings.
    """

    def __init__(self, dim: int = None) -> None:
        self.dim = dim or getattr(settings, "VECTOR_SIZE", 384)

    def _encode_one(self, text: str) -> List[float]:
        tokens = (text or "").lower().split()
        vec = [0.0] * self.dim

        if not tokens:
            return vec

        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=16).digest()
            for b in digest:
                idx = b % self.dim
                vec[idx] += 1.0 if (b % 2 == 0) else -1.0

        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def encode(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        if isinstance(texts, str):
            return self._encode_one(texts)
        return [self._encode_one(t) for t in texts]


@lru_cache(maxsize=1)
def get_encoder() -> Any:
    """
    Global encoder factory.

    - Local dev: if sentence-transformers is installed, returns a real
      SentenceTransformer model.
    - Render backend: falls back to HashedEncoder.
    """
    if settings.EMBEDDING_STRATEGY.lower() == "hashed":
        log.info("Using hashed fallback encoder (EMBEDDING_STRATEGY=hashed)")
        return HashedEncoder()

    if HAS_ST and SentenceTransformer is not None:
        if not settings.EMBEDDING_ALLOW_REMOTE_DOWNLOAD:
            log.warning(
                "EMBEDDING_ALLOW_REMOTE_DOWNLOAD is disabled; using hashed fallback encoder."
            )
            return HashedEncoder()
        log.info(f"Loading SentenceTransformer model: {settings.EMBEDDING_MODEL}")
        try:
            model = SentenceTransformer(settings.EMBEDDING_MODEL)
            return model
        except Exception as e:
            log.exception(
                "Failed to load SentenceTransformer, falling back to hashed encoder: %s",
                e,
            )
            return HashedEncoder()

    log.warning("sentence-transformers not available, using hashed fallback encoder")
    return HashedEncoder()
