"""
tools/check.py — generate_comprehension_check MCP tool.

Generates one targeted comprehension check question plus answer signals.
The signals travel with the question so assess_answer can evaluate the
user's response accurately — not just by keyword matching.
"""

from __future__ import annotations

import json
import logging

import openai

from config import get_settings
from models.schemas import GenerateCheckInput, GenerateCheckOutput
from prompts.templates import generate_check_prompt

logger = logging.getLogger(__name__)
settings = get_settings()

_client = openai.AsyncOpenAI(
    api_key=settings.groq_api_key,
    base_url="https://api.groq.com/openai/v1",
)


async def generate_comprehension_check(
    explanation: str,
    topic: str,
    key_concepts: list[str],
) -> dict:
    """
    Generate one comprehension check question grounded in the explanation.

    Args:
        explanation:  The explanation text from explain_concept.
        topic:        Canonical topic name from ExplainConceptOutput.topic.
        key_concepts: Key concepts from ExplainConceptOutput.key_concepts.

    Returns:
        GenerateCheckOutput as a dict:
        {
          "question":              Single targeted check question,
          "correct_signals":       Phrases indicating correct understanding,
          "misconception_signals": Phrases indicating a specific misconception,
          "hint":                  Gentle hint for stuck learners
        }
    """
    validated = GenerateCheckInput(
        explanation=explanation,
        topic=topic,
        key_concepts=key_concepts,
    )

    logger.info(
        "generate_comprehension_check called",
        topic=validated.topic,
        key_concepts=validated.key_concepts,
    )

    prompt = generate_check_prompt(
        explanation=validated.explanation,
        topic=validated.topic,
        key_concepts=validated.key_concepts,
    )

    response = await _client.chat.completions.create(
        model=settings.groq_model,
        max_tokens=768,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = (response.choices[0].message.content or "").strip()

    try:
        raw_dict = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(
            "generate_comprehension_check json parse failed",
            raw_preview=raw_text[:200],
            error=str(e),
        )
        return GenerateCheckOutput(
            question=f"Can you explain {validated.topic} in your own words?",
            correct_signals=[f"demonstrates understanding of {c}" for c in validated.key_concepts[:2]],
            misconception_signals=[],
            hint=f"Think about what {validated.topic} does and when you would use it.",
        ).model_dump()

    output = GenerateCheckOutput(**raw_dict)

    logger.info(
        "generate_comprehension_check succeeded",
        topic=validated.topic,
        correct_signals_count=len(output.correct_signals),
    )

    return output.model_dump()
