"""
app/services/mcp_client.py — FastMCP client wrapper.

WHY FASTMCP CLIENT INSTEAD OF RAW HTTPX:
  The MCP protocol (2024-11-05 spec) requires an initialize/initialized
  handshake before any tool calls can be made. Doing this correctly with
  raw httpx means reimplementing the handshake and session management.

  FastMCP's own Client class handles all of this correctly:
    - Sends the initialize request on connect
    - Manages session state
    - Speaks the correct wire format for streamable-http
    - Handles both streaming and non-streaming responses

  Since the MCP server already uses fastmcp, adding it to the backend
  too is a zero-friction choice.

LIFECYCLE:
  The client is connected once during app startup (lifespan) and
  disconnected on shutdown. This reuses the underlying HTTP connection
  rather than creating a new session per tool call.

  main.py lifespan:
    await mcp_client.startup()   ← before yield
    await mcp_client.shutdown()  ← after yield

INTERFACE:
  The four typed helper methods (explain_concept, generate_comprehension_check,
  assess_answer, update_skill_score) match the MCP tools exactly.
  All return plain Python dicts — callers don't need to know about MCP internals.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import MCPError
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class MCPClient:
    """
    Persistent async client for the MCP server.

    Call startup() once when the app starts, shutdown() when it stops.
    All tool call methods are safe to call from any async context after startup.
    """

    def __init__(self) -> None:
        self._client: Any = None  # fastmcp.Client, typed as Any to avoid import-time dep

    async def startup(self) -> None:
        """
        Connect to the MCP server and perform the initialize handshake.

        Called from main.py lifespan before the app starts serving requests.
        Logs a clear error and raises if the MCP server is unreachable.
        """
        from fastmcp import Client  # type: ignore[import-untyped]

        url = settings.mcp_server_url
        logger.info("mcp_client_connecting", url=url)

        try:
            self._client = Client(url)
            await self._client.__aenter__()
            logger.info("mcp_client_connected", url=url)
        except Exception as e:
            logger.error("mcp_client_connect_failed", url=url, error=str(e))
            raise MCPError("startup", f"Cannot connect to MCP server at {url}: {e}")

    async def shutdown(self) -> None:
        """Cleanly close the connection. Called from main.py lifespan."""
        if self._client is not None:
            try:
                await self._client.__aexit__(None, None, None)
                logger.info("mcp_client_disconnected")
            except Exception as e:
                logger.warning("mcp_client_shutdown_error", error=str(e))
            finally:
                self._client = None

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Call a named tool and return the parsed result dict.

        FastMCP Client returns a list of ContentBlock objects.
        Our tools always return a single TextContent block whose .text
        is a JSON string — we parse and return it.

        Raises MCPError on any failure.
        """
        if self._client is None:
            raise MCPError(tool_name, "MCP client not connected. Was startup() called?")

        logger.debug("mcp_tool_call", tool=tool_name)

        try:
            result = await self._client.call_tool(tool_name, arguments)
        except Exception as e:
            error_msg = str(e)
            logger.error("mcp_tool_failed", tool=tool_name, error=error_msg)
            raise MCPError(tool_name, error_msg)

        # result is a list of content blocks
        if not result:
            raise MCPError(tool_name, "MCP tool returned empty content")

        first = result[0]
        raw_text: str = getattr(first, "text", "")

        if not raw_text:
            raise MCPError(tool_name, "MCP tool returned no text content")

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as e:
            logger.error("mcp_parse_error", tool=tool_name, raw=raw_text[:200])
            raise MCPError(tool_name, f"Tool returned invalid JSON: {e}")

        logger.debug("mcp_tool_success", tool=tool_name)
        return parsed

    # ── Typed helpers ─────────────────────────────────────────────────────────

    async def explain_concept(
        self,
        question: str,
        code: str | None = None,
    ) -> dict[str, Any]:
        """
        Call explain_concept.
        Returns: {explanation, topic, key_concepts, code_example?, analogy?}
        """
        args: dict[str, Any] = {"question": question}
        if code:
            args["code"] = code
        return await self.call_tool("explain_concept", args)

    async def generate_comprehension_check(
        self,
        explanation: str,
        topic: str,
        key_concepts: list[str],
    ) -> dict[str, Any]:
        """
        Call generate_comprehension_check.
        Returns: {question, correct_signals, misconception_signals, hint}
        """
        return await self.call_tool(
            "generate_comprehension_check",
            {"explanation": explanation, "topic": topic, "key_concepts": key_concepts},
        )

    async def assess_answer(
        self,
        check_question: str,
        user_answer: str,
        explanation: str,
        correct_signals: list[str],
        misconception_signals: list[str],
        topic: str,
    ) -> dict[str, Any]:
        """
        Call assess_answer.
        Returns: {understood, score, feedback, misconception?, re_explain_angle?}
        """
        return await self.call_tool(
            "assess_answer",
            {
                "check_question": check_question,
                "user_answer": user_answer,
                "explanation": explanation,
                "correct_signals": correct_signals,
                "misconception_signals": misconception_signals,
                "topic": topic,
            },
        )

    async def update_skill_score(
        self,
        topic: str,
        current_score: float,
        current_attempts: int,
        understood: bool,
        assessment_score: int,
    ) -> dict[str, Any]:
        """
        Call update_skill_score (pure math, no LLM).
        Returns: {topic, old_score, new_score, delta, level, message, streak_increment}
        """
        return await self.call_tool(
            "update_skill_score",
            {
                "topic": topic,
                "current_score": current_score,
                "current_attempts": current_attempts,
                "understood": understood,
                "assessment_score": assessment_score,
            },
        )


# Module-level singleton — shared across all requests.
mcp_client = MCPClient()
