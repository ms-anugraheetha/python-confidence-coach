"""
api/v1/routes/health.py — Health check endpoint.

WHY THIS FILE EXISTS:
  Every production service needs a health endpoint. It's used by:
    - Docker: HEALTHCHECK instruction
    - Kubernetes: liveness and readiness probes
    - Load balancers: to decide whether to route traffic here
    - You: to confirm the server started correctly before testing anything else

  GET /health  → always returns 200 if the server process is alive.
  GET /health/ready → returns 200 only when DB connection is confirmed (Phase 4).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


class HealthResponse(BaseModel):
    status: str
    environment: str
    timestamp: str
    version: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    description="Returns 200 if the server process is running. No DB check.",
)
async def health_check() -> HealthResponse:
    """
    Lightweight liveness check.
    Does NOT check the database or external services — just confirms the
    Python process is alive and serving requests.
    """
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="0.1.0",
    )
