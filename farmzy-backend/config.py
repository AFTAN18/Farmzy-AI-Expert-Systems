from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "FARMZY Backend"
    app_version: str = "1.0.0"

    supabase_url: str = ""
    supabase_service_key: str = ""

    thingspeak_channel_id: str = "2972911"
    thingspeak_read_api_key: str = ""

    model_artifacts_dir: str = "./ml/artifacts"
    poll_interval_seconds: int = 60
    retrain_min_rows: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
