"""Logging configuration.

Log records never contain image content, file names of the biometric samples
or other personal data.  Only identifiers and numeric metrics are logged.
"""

from __future__ import annotations

import logging
import logging.config
import sys

from .config import settings

_FORMAT = "%(asctime)s %(levelname)-8s %(name)s | %(message)s"


def configure_logging() -> None:
    """Configure the root logger for the backend process."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {"format": _FORMAT},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": sys.stdout,
                },
            },
            "root": {"handlers": ["console"], "level": level},
            "loggers": {
                "uvicorn": {"handlers": ["console"], "level": level, "propagate": False},
                "uvicorn.access": {"handlers": ["console"], "level": level, "propagate": False},
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger."""
    return logging.getLogger(name)


__all__ = ["configure_logging", "get_logger"]
