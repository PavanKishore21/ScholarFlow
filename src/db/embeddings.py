# src/db/embeddings.py

from functools import lru_cache
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


class DummyEncoder:
    """
    Lightweight stand-in encoder for environments where
    sentence-transformers / torch are not available.

    It returns zero vectors of length settings.VECTOR_SIZE so the rest of
    the pipeline (Qdrant, etc.) can still work without crashing.
    """

    def __init__(self, dim: int = None) -> None:
        self.dim = dim or getattr(settings, "VECTOR_SIZE", 384)

    def encode(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        if isinstance(texts, str):
            return [0.0] * self.dim
        # assume iterable of strings
        return [[0.0] * self.dim for _ in texts]


@lru_cache(maxsize=1)
def get_encoder() -> Any:
    """
    Global encoder factory.

    - Local dev: if sentence-transformers is installed, returns a real
      SentenceTransformer model.
    - Render backend: falls back to DummyEncoder (no torch/transformers).
    """
    if HAS_ST and SentenceTransformer is not None:
        log.info(f"Loading SentenceTransformer model: {settings.EMBEDDING_MODEL}")
        try:
            model = SentenceTransformer(settings.EMBEDDING_MODEL)
            return model
        except Exception as e:
            log.exception(f"Failed to load SentenceTransformer, falling back to DummyEncoder: {e}")
            return DummyEncoder()

    log.warning("sentence-transformers not available, using DummyEncoder")
    return DummyEncoder()
