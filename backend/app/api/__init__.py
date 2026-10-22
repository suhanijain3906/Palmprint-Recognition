"""API layer of the backend."""

from .dependencies import (
    CurrentUser,
    DbSession,
    get_current_user,
    get_experiment_service,
    get_image_service,
    get_processing_service,
    get_report_service,
    get_storage,
)
from .routes import (
    artifacts_router,
    auth_router,
    comparison_router,
    datasets_router,
    experiments_router,
    health_router,
    images_router,
    processing_router,
    recognition_router,
    reports_router,
)

__all__ = [
    "CurrentUser",
    "DbSession",
    "artifacts_router",
    "auth_router",
    "comparison_router",
    "datasets_router",
    "experiments_router",
    "get_current_user",
    "get_experiment_service",
    "get_image_service",
    "get_processing_service",
    "get_report_service",
    "get_storage",
    "health_router",
    "images_router",
    "processing_router",
    "recognition_router",
    "reports_router",
]
