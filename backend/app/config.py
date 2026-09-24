from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EACIP"
    app_version: str = "0.1.0"
    app_env: str = "development"

    # In Docker: hostname "db" resolves to the postgres container.
    database_url: str = "postgresql+asyncpg://eacip:eacip_dev_password@db:5432/eacip"

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------
    llm_provider: str = "mock"
    # Allowed: "mock", "groq"

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"

    # ------------------------------------------------------------------
    # Requirement Engine
    # ------------------------------------------------------------------
    llm_requirement_confidence_threshold: float = 0.6
    """Reject LLM candidates below this confidence (0.0 - 1.0)."""

    llm_max_requirement_candidates: int = 5
    """Max number of candidate requirements the LLM may return."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()