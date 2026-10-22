"""Runtime configuration for the ML / computer-vision service."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment driven settings.

    Every value can be overridden with an ``ML_`` prefixed environment
    variable, e.g. ``ML_MAX_UPLOAD_BYTES=5242880``.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_prefix="ML_",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Palmprint ML Service"
    version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8001
    log_level: str = "INFO"

    # --- Internal service authentication -------------------------------
    service_api_key: str | None = None

    # --- Upload / decoding limits -------------------------------------
    max_upload_bytes: int = Field(default=12 * 1024 * 1024, ge=1024)
    max_pixels: int = Field(default=40_000_000, ge=1_000)
    max_dimension: int = Field(default=6000, ge=64)

    # --- Artifact handling --------------------------------------------
    artifact_dir: Path = Path("./data/artifacts")
    artifact_retention_hours: int = Field(default=24, ge=1)
    artifact_max_bytes: int = Field(default=8 * 1024 * 1024, ge=1024)

    # --- Trained model directory --------------------------------------
    model_dir: Path = Path("./models")

    # --- Algorithm defaults -------------------------------------------
    default_orb_features: int = Field(default=2000, ge=16, le=20000)
    default_lowe_ratio: float = Field(default=0.75, gt=0.0, lt=1.0)

    @property
    def supported_media_types(self) -> tuple[str, ...]:
        return ("image/png", "image/jpeg", "image/bmp", "image/tiff", "image/webp")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
