"""
config.py — MCP server settings loaded from environment variables.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    groq_api_key: str
    groq_model: str = "llama-3.1-8b-instant"

    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001

    environment: str = "development"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> MCPSettings:
    return MCPSettings()  # type: ignore[call-arg]
