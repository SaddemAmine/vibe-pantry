from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://localhost:5432/vibe_pantry"

    model_config = {"env_file": ".env"}


settings = Settings()
