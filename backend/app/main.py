"""Application entry point of the backend API.

The backend is responsible for input validation, storage, persistence, access
control and report generation.  All image processing is delegated to the
independent ML service over HTTP.

Concurrency model
-----------------
The endpoints that touch the database or the ML service are declared as
synchronous ``def`` functions.  Starlette executes them in a worker thread
pool, so the event loop is never blocked by synchronous I/O or by the CPU
work of the image processing chain.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import (
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
from .core.config import settings
from .core.logging import configure_logging
from .utils.errors import AppError

configure_logging()
logger = logging.getLogger("backend")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "%s %s starting in %s mode (auth %s, storage %s, ml %s)",
        settings.app_name,
        settings.version,
        settings.environment,
        "enabled" if settings.auth_enabled else "disabled",
        settings.storage_backend,
        settings.ml_service_url,
    )
    if settings.is_production and settings.secret_key == "change-me-in-production":
        raise RuntimeError("SECRET_KEY must be changed before running in production mode.")
    if settings.auto_create_schema:
        from .db.session import init_db

        init_db()
        logger.warning(
            "AUTO_CREATE_SCHEMA is enabled: tables were created without Alembic. "
            "Use 'alembic upgrade head' in production."
        )
    yield
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=(
            "REST API of the Palmprint Research Platform.\n\n"
            "The API manages uploads, processing jobs, experiments and reports. "
            "All image processing is performed by the independent ML service; "
            "this API never talks to the browser side of the ML service and "
            "never returns a fabricated recognition result."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    origins = list(settings.allowed_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=settings.allow_credentials and not settings.auth_enabled,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Service-Token"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning("%s %s -> %s: %s", request.method, request.url.path, exc.code, exc.message)
        return JSONResponse(status_code=exc.status_code, content=exc.to_payload())

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred while processing the request.",
                    "details": {},
                },
            },
        )

    app.include_router(health_router)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(images_router, prefix=settings.api_prefix)
    app.include_router(processing_router, prefix=settings.api_prefix)
    app.include_router(recognition_router, prefix=settings.api_prefix)
    app.include_router(comparison_router, prefix=settings.api_prefix)
    app.include_router(experiments_router, prefix=settings.api_prefix)
    app.include_router(datasets_router, prefix=settings.api_prefix)
    app.include_router(reports_router, prefix=settings.api_prefix)
    app.include_router(artifacts_router, prefix=settings.api_prefix)

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
