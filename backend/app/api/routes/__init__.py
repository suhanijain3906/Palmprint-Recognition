"""API routes of the backend."""

from .artifacts import router as artifacts_router
from .auth import router as auth_router
from .comparison import router as comparison_router
from .datasets import router as datasets_router
from .experiments import router as experiments_router
from .health import router as health_router
from .images import router as images_router
from .processing import router as processing_router
from .recognition import router as recognition_router
from .reports import router as reports_router

__all__ = [
    "artifacts_router",
    "auth_router",
    "comparison_router",
    "datasets_router",
    "experiments_router",
    "health_router",
    "images_router",
    "processing_router",
    "recognition_router",
    "reports_router",
]
