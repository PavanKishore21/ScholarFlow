# src/config.py

from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # --- External services (optional with safe defaults) ---
    GROQ_API_KEY: Optional[str] = None

    # Neo4j (often not available in cloud demo)
    NEO4J_URI: Optional[str] = None
    NEO4J_USERNAME: Optional[str] = None
    NEO4J_PASSWORD: Optional[str] = None

    # Qdrant
    # Default localhost for dev; override via env on Render
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None

    # --- Models ---
    LLM_SMART: str = "llama-3.3-70b-versatile"
    LLM_FAST: str = "llama-3.1-8b-instant"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # --- Vector store ---
    # all-MiniLM-L6-v2 has 384-dim embeddings
    COLLECTION_NAME: str = "scholarflow_chunks"
    VECTOR_SIZE: int = 384
    TOP_K_VECTOR: int = 6
    TOP_K_GRAPH: int = 4
    TOP_K_FINAL: int = 5

    # --- Chunking ---
    CHUNK_SIZE: int = 1200
    CHUNK_OVERLAP: int = 200

    # --- Payload schema versioning ---
    PAYLOAD_SCHEMA_VERSION: int = 2

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
