"""
tools/explain.py — explain_concept MCP tool.

WHAT THIS TOOL DOES:
  Receives a Python question (and optionally a code snippet), calls Gemini
  to generate a structured explanation, validates the response, and returns
  it as a typed ExplainConceptOutput.

HOW THIS TOOL IS CALLED:
  The MCP server calls this tool first, every time, for every user question.
  The system prompt enforces this — the outer model is not allowed to compose
  an explanation itself. It always delegates to this tool.

WHY THE TOOL CALLS AN LLM INTERNALLY:
  The tool has a focused, constrained prompt that produces consistent JSON.
  The outer conversation manages flow. This inner call manages explanation quality.
  They are separate concerns. Currently using Gemini via OpenAI-compatible endpoint.
"""

from __future__ import annotations

import json
import logging

import openai

from config import get_settings
from models.schemas import ExplainConceptInput, ExplainConceptOutput
from prompts.templates import explain_concept_prompt

logger = logging.getLogger(__name__)
settings = get_settings()

# Module-level client — created once, reused across all calls.
# Groq exposes an OpenAI-compatible endpoint so we use the openai SDK.
_client = openai.AsyncOpenAI(
    api_key=settings.groq_api_key,
    base_url="https://api.groq.com/openai/v1",
)


async def explain_concept(question: str, code: str | None = None) -> dict:
    """
    Generate a structured, beginner-friendly explanation of a Python concept.

    Args:
        question: The user's Python question or topic to explain.
        code:     Optional Python code snippet the user provided.
                  When present, the explanation references specific lines.

    Returns:
        ExplainConceptOutput as a dict:
        {
          "explanation":  Clear, beginner-friendly explanation (100-300 words),
          "topic":        Canonical topic name e.g. "decorators",
          "key_concepts": List of 2-4 core concepts,
          "code_example": Short illustrative code or None,
          "analogy":      Real-world analogy or None
        }
    """
    validated = ExplainConceptInput(question=question, code=code)

    logger.info(
        "explain_concept called",
        question_preview=validated.question[:80],
        has_code=validated.code is not None,
    )

    prompt = explain_concept_prompt(
        question=validated.question,
        code=validated.code,
    )

    # ── Inner Groq call ──────────────────────────────────────────────────────
    response = await _client.chat.completions.create(
        model=settings.groq_model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = (response.choices[0].message.content or "").strip()

    # ── Parse and validate ───────────────────────────────────────────────────
    try:
        raw_dict = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(
            "explain_concept json parse failed",
            raw_preview=raw_text[:200],
            error=str(e),
        )
        return ExplainConceptOutput(
            explanation=raw_text,
            topic=_infer_topic(validated.question),
            key_concepts=[],
            code_example=None,
            analogy=None,
        ).model_dump()

    output = ExplainConceptOutput(**raw_dict)

    logger.info(
        "explain_concept succeeded",
        topic=output.topic,
        key_concepts=output.key_concepts,
    )

    return output.model_dump()


def _infer_topic(question: str) -> str:
    """Fallback topic inference when JSON parsing fails."""
    q = question.lower()
    keyword_map = {
        "decorator": "decorators",
        "generator": "generators",
        "async": "async/await",
        "await": "async/await",
        "comprehension": "list comprehensions",
        "lambda": "lambda functions",
        "class": "classes",
        "inherit": "inheritance",
        "exception": "exception handling",
        "error": "exception handling",
        "dict": "dictionaries",
        "list": "lists",
        "tuple": "tuples",
        "set": "sets",
        "closure": "closures",
        "scope": "variable scope",
        "import": "modules and imports",
        "type hint": "type hints",
        "typing": "type hints",
    }
    for keyword, topic in keyword_map.items():
        if keyword in q:
            return topic
    return "python"
