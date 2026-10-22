"""Backend configuration.

Every setting can be provided through an environment variable (or a ``.env``
file).  Secrets are never baked into the image and are never sent to the
frontend.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment driven backend settings."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ----------------------------------------------------
    app_name: str = "Palmprint Research Platform API"
    version: str = "0.1.0"
    environment: Literal["development", "testing", "production"] = "development"
    api_prefix: str = "/api/v1"
    debug: bool = False
    log_level: str = "INFO"

    # --- Database -------------------------------------------------------
    database_url: str = "sqlite:///./data/palmprint.db"
    sql_echo: bool = False
    auto_create_schema: bool = False

    # --- Storage --------------------------------------------------------
    storage_backend: Literal["local", "s3"] = "local"
    storage_root: Path = Path("./data/storage")
    s3_bucket: str | None = None
    s3_endpoint_url: str | None = None
    s3_region: str = "us-east-1"
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_use_path_style: bool = True

    # --- Uploads --------------------------------------------------------
    max_upload_bytes: int = Field(default=12 * 1024 * 1024, ge=1024)
    max_image_pixels: int = Field(default=40_000_000, ge=1_000)
    retention_days: int = Field(default=30, ge=0)

    # --- Security -------------------------------------------------------
    auth_enabled: bool = False
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = Field(default=720, ge=1)
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
        ]
    )
    allow_credentials: bool = False
    demo_mode: bool = True
    allow_registration: bool = True

    # --- ML service -----------------------------------------------------
    ml_service_url: str = "http://localhost:8001"
    ml_service_timeout: float = Field(default=60.0, gt=0)
    ml_service_api_key: str | None = None

    # --- Datasets -------------------------------------------------------
    dataset_root: Path = Path("./data/datasets")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Allow a comma separated list in the environment variable."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
