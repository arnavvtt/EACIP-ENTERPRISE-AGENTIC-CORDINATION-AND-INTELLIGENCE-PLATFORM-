from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "EACIP"
    app_version: str = "0.1.0"
    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://eacip:eacip_dev_password@localhost:5432/eacip"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()