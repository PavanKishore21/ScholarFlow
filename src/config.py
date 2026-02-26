# src/config.py

from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # --- External services (optional with safe defaults) ---
    GROQ_API_KEY: Optional[str] = None
    ADMIN_API_TOKEN: Optional[str] = None

    # Neo4j (often not available in cloud demo)
    NEO4J_URI: Optional[str] = None
    NEO4J_USERNAME: Optional[str] = None
    NEO4J_PASSWORD: Optional[str] = None

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    CORS_ALLOWED_ORIGINS: str = "*"

    # --- Models ---
    LLM_SMART: str = "llama-3.3-70b-versatile"
    LLM_FAST: str = "llama-3.1-8b-instant"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_ALLOW_REMOTE_DOWNLOAD: bool = False
    EMBEDDING_STRATEGY: str = "auto"  # auto | hashed

    # --- Vector store ---
    COLLECTION_NAME: str = "scholarflow_chunks"
    VECTOR_SIZE: int = 384        # all-MiniLM-L6-v2 is 384-dim
    TOP_K_VECTOR: int = 6
    TOP_K_GRAPH: int = 4
    TOP_K_FINAL: int = 5

    # --- Chunking ---
    CHUNK_SIZE: int = 1200
    CHUNK_OVERLAP: int = 200

    # --- Payload schema versioning ---
    PAYLOAD_SCHEMA_VERSION: int = 2

    # --- API behavior ---
    MAX_UPLOAD_SIZE_MB: int = 20
    ENABLE_DEBUG_ENDPOINT: bool = False
    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
