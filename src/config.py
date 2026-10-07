"""Configuración tipada del proyecto. Carga variables desde .env."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Aplicación
    app_name: str = "data-intelligence-platform"
    app_env: str = "development"
    app_debug: bool = True
    log_level: str = "INFO"
    timezone: str = "UTC"

    # Data Lake
    data_lake_root: Path = Field(default=Path("./data"))
    data_lake_raw_dir: Path = Field(default=Path("./data/raw"))
    data_lake_bronze_dir: Path = Field(default=Path("./data/bronze"))
    data_lake_silver_dir: Path = Field(default=Path("./data/silver"))
    data_lake_gold_dir: Path = Field(default=Path("./data/gold"))
    data_lake_quarantine_dir: Path = Field(default=Path("./data/quarantine"))
    data_lake_metadata_dir: Path = Field(default=Path("./data/metadata"))

    # S3 / MinIO
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key_id: str = "minioadmin"
    s3_secret_access_key: str = "minioadmin"
    s3_bucket_raw: str = "maritime-raw"
    s3_bucket_bronze: str = "maritime-bronze"
    s3_region: str = "us-east-1"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "maritime"
    postgres_user: str = "maritime_user"
    postgres_password: str = "change_me_dev_only"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
