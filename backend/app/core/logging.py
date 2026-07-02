"""
app/core/logging.py — Structured logging setup.

WHY THIS FILE EXISTS:
  Standard Python logging outputs unstructured strings. In production, you
  need key-value structured logs (JSON) so log aggregators can search, filter,
  and alert on specific fields.

  This file:
    1. Configures structlog with the right processors for each environment.
    2. Provides a RequestIDMiddleware that stamps every log line with the
       incoming request's unique ID — essential for tracing bugs in production.
    3. Exposes `get_logger()` as the single way to get a logger anywhere.

USAGE:
  from app.core.logging import get_logger
  logger = get_logger(__name__)
  logger.info("user_asked_question", user_id=42, topic="decorators")
"""

from __future__ import annotations

import logging
import sys
import uuid
from collections.abc import Callable
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.config import get_settings

# The context variable key used to carry the request ID through async code.
# structlog's AsyncBoundLogger reads this automatically.
REQUEST_ID_KEY = "request_id"


def configure_logging() -> None:
    """
    Call this once at application startup (in main.py's lifespan).

    Sets up structlog processors, ties it into stdlib logging (so third-party
    libraries that use `logging.getLogger` also output structured logs), and
    selects the right renderer for the current environment.
    """
    settings = get_settings()

    # ── Shared processors ────────────────────────────────────────────────────
    # These run on every log event regardless of environment.
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        # ^ Merges context variables bound with `structlog.contextvars.bind_contextvars()`
        # This is how the request_id gets attached to every log line automatically.

        structlog.stdlib.add_logger_name,
        # ^ Adds {"logger": "app.services.coach_service"} to every event.

        structlog.stdlib.add_log_level,
        # ^ Adds {"level": "info"} to every event.

        structlog.stdlib.PositionalArgumentsFormatter(),
        # ^ Handles logger.info("Hello %s", "world") style calls.

        structlog.processors.TimeStamper(fmt="iso"),
        # ^ Adds {"timestamp": "2025-01-01T12:00:00.000Z"} in ISO 8601.

        structlog.processors.StackInfoRenderer(),
        # ^ Attaches stack info when log_kwargs include stack_info=True.

        structlog.processors.format_exc_info,
        # ^ Formats exception tracebacks as a string in the JSON output.
    ]

    # ── Environment-specific renderer ────────────────────────────────────────
    if settings.is_production:
        # JSON output — one log event per line, parseable by log aggregators.
        renderer = structlog.processors.JSONRenderer()
    else:
        # Color-coded, indented output for human reading in the terminal.
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [
            # Bridge to stdlib: lets structlog events pass through stdlib handlers.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
        # ^ Cache the bound logger after the first call — small performance win.
    )

    # ── Configure stdlib logging (for third-party libraries) ─────────────────
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
        # ^ Third-party log records also go through shared_processors before rendering.
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(getattr(logging, settings.log_level))

    # Reduce noise from chatty third-party loggers.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a named structured logger.

    Usage:
        logger = get_logger(__name__)
        logger.info("event_name", key="value", another_key=42)

    In production this emits:
        {"level": "info", "event": "event_name", "key": "value", "another_key": 42,
         "timestamp": "...", "request_id": "...", "logger": "app.services.coach"}

    In development this emits a color-coded line to your terminal.
    """
    return structlog.get_logger(name)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that assigns a unique ID to every incoming request.

    The ID is:
      1. Read from the X-Request-ID header if the client provided one.
         (Useful when a gateway or load balancer stamps IDs upstream.)
      2. Generated as a UUID4 if the header is absent.

    The ID is then:
      - Stored in structlog's context variables so every log line emitted
        during this request automatically includes {"request_id": "..."}.
      - Returned in the X-Request-ID response header so the frontend
        can report it in bug tickets.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._logger = get_logger(__name__)

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        # Use upstream ID if provided, otherwise generate a fresh one.
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Bind the request_id to structlog's async context.
        # Every log call within this request's async task will include it.
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        self._logger.info(
            "request_started",
            client=request.client.host if request.client else "unknown",
        )

        response = await call_next(request)

        self._logger.info(
            "request_finished",
            status_code=response.status_code,
        )

        # Return the ID in the response so clients can reference it.
        response.headers["X-Request-ID"] = request_id
        return response
