"""
app/core/config.py — Application settings loaded from environment variables.

WHY THIS FILE EXISTS:
  Every configuration value lives here, typed and validated by Pydantic.
  No os.getenv() calls are scattered across the codebase — everything goes
  through `get_settings()`. This means:
    1. A missing required variable crashes at startup, not at request time.
    2. Tests can override settings by patching a single function.
    3. New developers read one file to understand what the app needs.

USAGE:
  from app.core.config import get_settings
  settings = get_settings()
  print(settings.database_url)
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Typed, validated application configuration.

    Pydantic reads these values from environment variables or a .env file.
    If a field has no default and is missing from the environment, the app
    will raise a ValidationError at startup — this is intentional.
    """

    model_config = SettingsConfigDict(
        env_file=".env",            # Read from .env in the working directory
        env_file_encoding="utf-8",
        case_sensitive=False,       # DATABASE_URL and database_url both work
        extra="ignore",             # Ignore unknown vars (personal .env entries)
    )

    # ── Application ───────────────────────────────────────────────────────────

    app_name: str = "Python Confidence Coach"
    environment: Literal["development", "production", "test"] = "development"

    # ── Security ──────────────────────────────────────────────────────────────

    secret_key: str = Field(..., min_length=32)
    # ^ The `...` means required — no default. min_length=32 enforces strength.

    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_not_be_placeholder(cls, v: str) -> str:
        """
        Prevent someone from running with the .env.example placeholder value.
        This validator runs at startup — failing fast is better than failing silently.
        """
        if "change-me" in v.lower():
            raise ValueError(
                "SECRET_KEY still contains 'change-me'. "
                "Generate a real secret with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v

    # ── Database ──────────────────────────────────────────────────────────────

    database_url: str = Field(
        ...,
        description="PostgreSQL async connection string. Must start with postgresql+asyncpg://",
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20

    @field_validator("database_url")
    @classmethod
    def database_url_must_be_async(cls, v: str) -> str:
        """
        SQLAlchemy needs the +asyncpg driver prefix for async operation.
        If someone pastes a sync URL, catch it here with a helpful message.
        """
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use the async driver: postgresql+asyncpg://... "
                "(not postgresql:// or postgres://)"
            )
        return v

    # ── Groq ──────────────────────────────────────────────────────────────────

    groq_api_key: str = Field(..., description="Groq API key. Get one free at console.groq.com")

    # ── MCP server ────────────────────────────────────────────────────────────

    mcp_server_url: str = Field(
        default="http://localhost:8001/mcp",
        description="Base URL of the FastMCP tool server (mcp_client connects here).",
    )
    mcp_timeout_seconds: int = 30

    # ── CORS ──────────────────────────────────────────────────────────────────

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """
        Allow CORS_ORIGINS to be either a JSON list or a comma-separated string
        in the .env file.

        .env file formats that both work:
          CORS_ORIGINS=http://localhost:5173,http://localhost:3000
          CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
        """
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ── Logging ───────────────────────────────────────────────────────────────

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ── Computed properties ───────────────────────────────────────────────────

    @computed_field  # type: ignore[misc]
    @property
    def is_production(self) -> bool:
        """True when running in production. Used to toggle strict CORS, JSON logging, etc."""
        return self.environment == "production"

    @computed_field  # type: ignore[misc]
    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @computed_field  # type: ignore[misc]
    @property
    def is_test(self) -> bool:
        return self.environment == "test"


@lru_cache
def get_settings() -> Settings:
    """
    Return the cached Settings instance.

    @lru_cache ensures the .env file is read exactly once — not on every
    function call. This makes tests easy: mock `get_settings` to return
    a Settings object with test values.

    Usage in a FastAPI dependency:
        from fastapi import Depends
        from app.core.config import get_settings, Settings

        def some_route(settings: Settings = Depends(get_settings)):
            ...

    Usage outside FastAPI (services, scripts):
        from app.core.config import get_settings
        settings = get_settings()
    """
    return Settings()  # type: ignore[call-arg]
