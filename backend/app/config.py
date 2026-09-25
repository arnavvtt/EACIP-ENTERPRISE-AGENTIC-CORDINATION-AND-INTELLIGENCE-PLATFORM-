from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    app_name: str = "EACIP"
    app_version: str = "0.1.0"
    app_env: str = "development"

    # Database
    database_url: str = "postgresql+asyncpg://eacip:eacip_dev_password@db:5432/eacip"

    # LLM
    llm_provider: str = "mock"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"

    # Requirement Engine
    llm_requirement_confidence_threshold: float = 0.6
    llm_max_requirement_candidates: int = 5

    # Embeddings (Stage 10)
    embedding_provider: str = "mock"
    # Allowed: "mock", "voyage"

    voyage_api_key: str = ""
    voyage_base_url: str = "https://api.voyageai.com/v1"
    embedding_model: str = "voyage-4-lite"

    # Chunking (Stage 10.3)
    chunk_size: int = 500
    chunk_overlap: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()