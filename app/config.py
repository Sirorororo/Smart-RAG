from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Model configs
    QWEN_VL_MODEL: str
    QWEN_EMBED_MODEL: str

    # Chunking configs
    CHUNK_SIZE: int = 1200
    CHUNK_OVERLAP: int = 200

    # Qdrant configs
    QDRANT_URL: str
    QDRANT_COLLECTION: str = "pdf_ingestion"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Singleton settings instance
settings = Settings()
