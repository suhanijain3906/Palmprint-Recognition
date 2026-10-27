"""Backend configuration.

Every setting can be provided through an environment variable (or a ``.env``
file).  Secrets are never baked into the image and are never sent to the
frontend.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

#: Public URL of the ML service deployed alongside the backend on Render.
#: Used only as a fallback when ``ML_SERVICE_URL`` is not configured.
_RENDER_ML_SERVICE_URL = "https://palmprint-recognition-1.onrender.com"


def _is_render() -> bool:
    return bool(
        os.getenv("RENDER", "").strip().lower() in {"1", "true", "yes"}
        or os.getenv("RENDER_SERVICE_ID")
        or os.getenv("RENDER_EXTERNAL_HOSTNAME")
        or os.getenv("RENDER_SERVICE_NAME")
        or os.getenv("RENDER_INSTANCE_ID")
    )


def _default_ml_service_url() -> str:
    return _RENDER_ML_SERVICE_URL if _is_render() else "http://localhost:8001"


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
    version: str = "0.1.1"
    environment: Literal["development", "testing", "production"] = "development"
    api_prefix: str = "/api/v1"
    debug: bool = False
    log_level: str = "INFO"

    # --- Database -------------------------------------------------------
    database_url: str = "sqlite:///./data/palmprint.db"
    sql_echo: bool = False
    auto_create_schema: bool = False
    auto_migrate: bool = True

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
    #: Comma separated list, JSON array or ``*``.  ``*`` is only honoured while
    #: authentication is disabled (the academic demo mode); authenticated
    #: deployments must list their frontend origins explicitly.
    allowed_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["*"])
    allow_credentials: bool = False
    demo_mode: bool = True
    allow_registration: bool = True

    # --- ML service -----------------------------------------------------
    ml_service_url: str = Field(default_factory=_default_ml_service_url)
    ml_service_timeout: float = Field(default=120.0, gt=0)
    ml_service_api_key: str | None = None

    # --- Datasets -------------------------------------------------------
    dataset_root: Path = Path("./data/datasets")

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalise_database_url(cls, value: object) -> object:
        """Translate managed-provider URLs to the installed psycopg driver."""
        if isinstance(value, str):
            if value.startswith("postgres://"):
                return "postgresql+psycopg://" + value[len("postgres://") :]
            if value.startswith("postgresql://"):
                return "postgresql+psycopg://" + value[len("postgresql://") :]
        return value

    @field_validator("debug", mode="before")
    @classmethod
    def _parse_debug(cls, value: object) -> bool:
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on", "debug")
        return bool(value)

    @field_validator("ml_service_url", mode="before")
    @classmethod
    def _clean_ml_service_url(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip().rstrip("/")
            if not value:
                return _default_ml_service_url()
            return value
        return value

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Accept ``*``, a comma separated list or a JSON array."""
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
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
