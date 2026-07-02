"""
app/main.py — FastAPI application factory.

HOW TO RUN:
  Development (auto-reload):
    uvicorn app.main:app --reload --port 8000

  Production:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import RequestIDMiddleware, configure_logging, get_logger

logger = get_logger(__name__)
settings = get_settings()


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages resources that live for the full duration of the application.

    Code BEFORE yield  → runs on startup.
    Code AFTER yield   → runs on shutdown (always, even on crash).
    """
    # ── Startup ───────────────────────────────────────────────────────────────
    configure_logging()

    logger.info(
        "application_starting",
        environment=settings.environment,
        version="0.1.0",
    )

    from app.db.session import init_db, close_db
    from app.services.mcp_client import mcp_client

    await init_db()
    await mcp_client.startup()
    logger.info("application_ready", host="0.0.0.0", port=9000)

    yield

    logger.info("application_shutting_down")
    await mcp_client.shutdown()
    await close_db()
    logger.info("application_stopped")


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description=(
            "An AI coaching chatbot that explains Python concepts, "
            "then checks your understanding with a single targeted question."
        ),
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    _register_middleware(app)
    _register_exception_handlers(app)
    _register_routers(app)

    return app


# ── Middleware ────────────────────────────────────────────────────────────────

def _register_middleware(app: FastAPI) -> None:
    """
    Register middleware in the correct order.

    IMPORTANT: Middleware runs in REVERSE registration order.
    The last-registered middleware wraps the outermost layer.

    Order (outermost → innermost):
      1. CORSMiddleware      ← must be outermost to handle OPTIONS preflight
      2. RequestIDMiddleware ← stamps every log line with a request ID
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    app.add_middleware(RequestIDMiddleware)


# ── Exception handlers ────────────────────────────────────────────────────────

def _register_exception_handlers(app: FastAPI) -> None:
    """Register handlers that translate exceptions → consistent JSON responses."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        log_fn = logger.warning if exc.http_status < 500 else logger.error
        log_fn(
            "domain_exception",
            exc_type=type(exc).__name__,
            code=exc.code,
            message=exc.message,
            status=exc.http_status,
        )
        return JSONResponse(
            status_code=exc.http_status,
            content=exc.to_response().model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        error_details: dict[str, Any] = {}
        for error in exc.errors():
            field_path = " → ".join(str(loc) for loc in error["loc"] if loc != "body")
            error_details[field_path] = error["msg"]

        logger.warning(
            "request_validation_error",
            errors=error_details,
            path=str(request.url.path),
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "code": "REQUEST_VALIDATION_ERROR",
                "message": "The request body contains invalid or missing fields.",
                "details": error_details,
            },
        )

    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_handler(
        request: Request, exc: PydanticValidationError
    ) -> JSONResponse:
        logger.error(
            "internal_validation_error",
            errors=exc.errors(),
            path=str(request.url.path),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred. Please try again.",
                "details": {},
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            "unhandled_exception",
            exc_type=type(exc).__name__,
            exc_message=str(exc),
            path=str(request.url.path),
            exc_info=True,
        )

        message = (
            f"Unhandled error: {exc!s}"
            if settings.is_development
            else "An unexpected error occurred. Please try again."
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": "INTERNAL_ERROR",
                "message": message,
                "details": {},
            },
        )


# ── Routers ───────────────────────────────────────────────────────────────────

def _register_routers(app: FastAPI) -> None:
    """Mount all API routers."""
    from app.api.v1.routes.health import router as health_router
    from app.api.v1.routes.auth import router as auth_router
    from app.api.v1.routes.chat import router as chat_router
    from app.api.v1.routes.conversations import router as conversations_router
    from app.api.v1.routes.dashboard import router as dashboard_router

    # Prefix-free health check
    app.include_router(health_router, tags=["health"])

    # Versioned API routes
    app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
    app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
    app.include_router(conversations_router, prefix="/api/v1", tags=["conversations"])
    app.include_router(dashboard_router, prefix="/api/v1", tags=["dashboard"])


# ── Module-level app instance ─────────────────────────────────────────────────
# uvicorn needs a module-level name to import: `uvicorn app.main:app`
app = create_app()
