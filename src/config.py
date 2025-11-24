from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str
    NEO4J_URI: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str
    QDRANT_URL: str
    QDRANT_API_KEY: str | None = None

    # Models
    LLM_SMART: str = "llama-3.3-70b-versatile"
    LLM_FAST: str = "llama-3.1-8b-instant"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Vector store
    COLLECTION_NAME: str = "arxiv_papers"
    VECTOR_SIZE: int = 384

    # Retrieval
    TOP_K_VECTOR: int = 8
    TOP_K_GRAPH: int = 4
    TOP_K_FINAL: int = 5

    # Chunking
    CHUNK_SIZE: int = 1200
    CHUNK_OVERLAP: int = 200

        # Payload schema versioning
    PAYLOAD_SCHEMA_VERSION: int = 2


    class Config:
        env_file = ".env"

settings = Settings()
