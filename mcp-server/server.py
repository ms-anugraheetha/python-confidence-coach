"""
server.py — FastMCP server entry point.

WHAT THIS FILE DOES:
  1. Creates the FastMCP application.
  2. Registers all four MCP tools with @mcp.tool().
  3. Starts an HTTP server (streamable-http transport) on port 8001.

HOW TOOLS ARE REGISTERED:
  @mcp.tool() reads the function's:
    - Name         → the tool name Claude calls (e.g. "explain_concept")
    - Type hints   → generates the JSON schema Claude sees in tools/list
    - Docstring    → the tool description sent to Claude

  The schema is what Claude uses to know WHAT arguments to pass.
  The description is what Claude uses to know WHEN to call the tool.

HOW THE BACKEND CONNECTS:
  The backend (mcp_client.py) sends HTTP requests to this server:
    GET  /mcp/tools          → lists all registered tools + schemas
    POST /mcp/tools/{name}   → calls a specific tool with arguments

  The backend is the MCP CLIENT. This server is the MCP SERVER.
  Claude runs in the backend — it never talks to this server directly.

HOW TO RUN:
  cd mcp-server
  uv sync
  cp .env.example .env  # fill in GROQ_API_KEY
  uv run python server.py
  # Server starts on http://0.0.0.0:8001
"""

from __future__ import annotations

import logging

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from config import get_settings
from tools.explain import explain_concept
from tools.check   import generate_comprehension_check
from tools.assess  import assess_answer
from tools.skill   import update_skill_score

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Create the MCP server ─────────────────────────────────────────────────────

mcp = FastMCP(
    name="Python Confidence Coach",
    instructions=(
        "I am the Python Confidence Coach MCP server. "
        "I provide four tools that implement the confidence loop: "
        "explain a concept, generate a comprehension check, assess the user's answer, "
        "and update their skill score. "
        "Always call these tools in order: explain → check → (user answers) → assess → score."
    ),
)


# ── Health check ──────────────────────────────────────────────────────────────
# A plain HTTP route (not an MCP tool) so Render/Docker/load balancers can
# poll liveness without speaking the MCP protocol. render.yaml's
# healthCheckPath expects exactly this route.

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})

# ── Register tools ────────────────────────────────────────────────────────────
# Each decorator call:
#   1. Registers the function as an MCP tool.
#   2. Reads type annotations → generates JSON schema for Claude.
#   3. Reads docstring → sends as tool description to Claude.
#
# The order here is the order tools appear in tools/list — Claude reads
# them in this order, which subtly reinforces the intended call sequence.

@mcp.tool()
async def explain_concept_tool(question: str, code: str | None = None) -> dict:
    """
    Generate a structured, beginner-friendly explanation of a Python concept or code snippet.

    Call this FIRST when the user asks any Python question.
    Returns an explanation, the canonical topic name, key concepts, a code example, and an analogy.
    The topic name must be passed to generate_comprehension_check and update_skill_score.

    Args:
        question: The user's Python question. Can be a concept, doubt, or code problem.
        code:     Optional Python code snippet the user provided.
    """
    return await explain_concept(question=question, code=code)


@mcp.tool()
async def generate_comprehension_check_tool(
    explanation: str,
    topic: str,
    key_concepts: list[str],
) -> dict:
    """
    Generate one comprehension check question grounded in the explanation just given.

    Call this IMMEDIATELY after explain_concept. Do not skip this step.
    Returns a targeted question plus correct-answer and misconception signals
    that assess_answer will use to evaluate the user's response.

    Args:
        explanation:  The explanation text returned by explain_concept.
        topic:        Topic name from explain_concept output.
        key_concepts: Key concepts list from explain_concept output.
    """
    return await generate_comprehension_check(
        explanation=explanation,
        topic=topic,
        key_concepts=key_concepts,
    )


@mcp.tool()
async def assess_answer_tool(
    check_question: str,
    user_answer: str,
    explanation: str,
    correct_signals: list[str],
    misconception_signals: list[str],
    topic: str,
) -> dict:
    """
    Assess whether the user genuinely understood the concept based on their answer.

    Call this after the user responds to the comprehension check question.
    If understood=True:  call update_skill_score, then affirm.
    If understood=False: re-explain from re_explain_angle, then call generate_comprehension_check again.

    Args:
        check_question:       The question that was asked.
        user_answer:          Exactly what the user typed.
        explanation:          The original explanation for full context.
        correct_signals:      From generate_comprehension_check output.
        misconception_signals: From generate_comprehension_check output.
        topic:                Python topic name.
    """
    return await assess_answer(
        check_question=check_question,
        user_answer=user_answer,
        explanation=explanation,
        correct_signals=correct_signals,
        misconception_signals=misconception_signals,
        topic=topic,
    )


@mcp.tool()
async def update_skill_score_tool(
    topic: str,
    current_score: float,
    current_attempts: int,
    understood: bool,
    assessment_score: int,
) -> dict:
    """
    Recalculate the user's skill score for a topic after a correct answer.

    Call this ONLY when assess_answer returns understood=True.
    Returns the new score, skill level, score delta, and a coaching message.
    The backend will persist new_score to the database.

    Args:
        topic:            Python topic name.
        current_score:    User's current score from the database (0–100).
        current_attempts: Total previous assessments for this topic.
        understood:       Must be True (from assess_answer output).
        assessment_score: Score 0–100 from assess_answer output.
    """
    return await update_skill_score(
        topic=topic,
        current_score=current_score,
        current_attempts=current_attempts,
        understood=understood,
        assessment_score=assessment_score,
    )


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    logger.info(
        "Starting MCP server",
        host=settings.mcp_host,
        port=settings.mcp_port,
        environment=settings.environment,
        tools=["explain_concept", "generate_comprehension_check", "assess_answer", "update_skill_score"],
    )
    mcp.run(
        transport="streamable-http",
        host=settings.mcp_host,
        port=settings.mcp_port,
        # FastMCP validates the Host header by default and rejects anything
        # that isn't localhost/127.0.0.1 (DNS-rebinding protection). This
        # server is only ever called internally (Render health checks +
        # the backend's mcp_client), never directly by a browser, so it's
        # safe to disable — equivalent validation happens at Render's network
        # layer. Without this, every request 421s with "Misdirected Request".
        host_origin_protection=False,
    )


if __name__ == "__main__":
    main()
