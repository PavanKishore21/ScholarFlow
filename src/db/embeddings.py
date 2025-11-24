from sentence_transformers import SentenceTransformer
from src.config import settings

_encoder = None

def get_encoder():
    global _encoder
    if _encoder is None:
        _encoder = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _encoder
