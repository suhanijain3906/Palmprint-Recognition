"""Application entry point of the ML / computer-vision service.

The service is intentionally standalone: it owns the image decoding, the
algorithms and the evaluation maths.  The backend talks to it over HTTP and
the browser never talks to it directly.
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.health import router as health_router
from .api.routes import artifact_store
from .api.routes import router as processing_router
from .config import settings
from .utils.errors import MLServiceError

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
)
logger = logging.getLogger("ml-service")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    artifact_store.root.mkdir(parents=True, exist_ok=True)
    logger.info(
        "%s %s started - artifacts in %s, model dir %s",
        settings.app_name,
        settings.version,
        artifact_store.root,
        settings.model_dir,
    )
    yield
    removed = artifact_store.cleanup_expired()
    logger.info("Shutdown complete, %s expired artefact(s) removed", removed)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=(
            "Computer vision and machine learning microservice for the Palmprint "
            "Research Platform.\n\n"
            "This service implements classical, documented image processing "
            "pipelines. It ships **without trained biometric weights**; every "
            "recognition response states whether a trained model was used."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # The ML service is an internal component.  CORS is therefore disabled by
    # default and only enabled explicitly for local debugging.
    if settings.log_level.upper() == "DEBUG":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:5173"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.exception_handler(MLServiceError)
    async def ml_error_handler(request: Request, exc: MLServiceError) -> JSONResponse:
        logger.warning("ML error on %s: %s", request.url.path, exc.message)
        return JSONResponse(status_code=exc.status_code, content=exc.to_payload())

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred while processing the request.",
                    "details": {"path": request.url.path},
                },
            },
        )

    @app.middleware("http")
    async def access_logging(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        duration = (time.perf_counter() - started) * 1000
        logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )
        response.headers["X-Processing-Time-Ms"] = f"{duration:.3f}"
        return response

    if settings.service_api_key:
        import hmac

        async def require_service_token(request: Request, call_next):
            """Protect every processing endpoint behind a shared service token.

            ``/health`` stays open so that container health checks keep
            working.  The browser never reaches this service: only the
            backend is expected to call it, and the backend already sends
            the ``X-Service-Token`` header.
            """
            if request.url.path == "/health":
                return await call_next(request)
            supplied = request.headers.get("X-Service-Token", "")
            if not hmac.compare_digest(supplied, settings.service_api_key):
                return JSONResponse(
                    status_code=401,
                    content={
                        "status": "error",
                        "error": {
                            "code": "unauthorized",
                            "message": "A valid service token is required to use this API.",
                            "details": {},
                        },
                    },
                )
            return await call_next(request)

        app.middleware("http")(require_service_token)

    app.include_router(health_router)
    app.include_router(processing_router, prefix=settings.api_prefix)
    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)
