"""
models/schemas.py — Pydantic input/output schemas for all four MCP tools.

WHY THIS FILE EXISTS:
  Every MCP tool has a typed contract:
    - Input schema  → FastMCP reads this to generate the JSON schema Claude sees.
                      Claude uses the schema to know what arguments to pass.
    - Output schema → FastMCP validates tool return values against this.
                      Prevents malformed results reaching Claude.

  Keeping schemas in one file means:
    - One place to change a tool's interface.
    - The test file can import all schemas without touching tool logic.
    - The backend (mcp_client.py) imports output schemas to parse tool results.

SCHEMA DESIGN PRINCIPLES:
  1. No Optional fields on inputs unless genuinely optional.
     A missing required field should fail at schema validation, not inside the tool.
  2. Output fields are always present — no Optional in outputs.
     Claude's parser shouldn't have to handle absent fields.
  3. Every field has a description. FastMCP includes descriptions in the JSON schema
     Claude receives — this is how Claude knows what to put in each field.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ═════════════════════════════════════════════════════════════════════════════
# Tool 1 — explain_concept
# ═════════════════════════════════════════════════════════════════════════════

class ExplainConceptInput(BaseModel):
    """
    Input Claude provides when calling explain_concept.

    Claude passes the user's raw question (and optionally their code).
    The tool generates a structured explanation from these.
    """

    question: str = Field(
        ...,
        description=(
            "The user's Python question or topic to explain. "
            "Can be a concept ('How do decorators work?'), "
            "a specific doubt ('What does *args mean?'), "
            "or a description of a code problem."
        ),
        min_length=3,
        max_length=2000,
    )

    code: str | None = Field(
        default=None,
        description=(
            "Optional Python code snippet the user provided. "
            "When present, the explanation will reference specific lines. "
            "When absent, the explanation uses illustrative examples."
        ),
        max_length=5000,
    )


class ExplainConceptOutput(BaseModel):
    """
    Structured explanation returned to Claude after the tool executes.

    Claude uses this to compose its response message to the user.
    The `topic` field is critical — it's passed to generate_comprehension_check
    and later used to update the skill score for the right topic.
    """

    explanation: str = Field(
        description="Clear, beginner-friendly explanation. Uses plain language, no jargon."
    )

    topic: str = Field(
        description=(
            "Canonical Python topic name, lowercase, e.g. 'decorators', 'list comprehensions', "
            "'generators', 'async/await'. Used to track skill progress."
        )
    )

    key_concepts: list[str] = Field(
        description="2–4 core concepts the user must grasp to understand the topic."
    )

    code_example: str | None = Field(
        description=(
            "A short illustrative code example (10–20 lines). "
            "None if the user's own code already serves as the example."
        )
    )

    analogy: str | None = Field(
        description=(
            "Optional real-world analogy that makes the concept intuitive. "
            "e.g. 'A decorator is like gift-wrapping a function.'"
        )
    )


# ═════════════════════════════════════════════════════════════════════════════
# Tool 2 — generate_comprehension_check
# ═════════════════════════════════════════════════════════════════════════════

class GenerateCheckInput(BaseModel):
    """
    Input for generating the comprehension check question.

    Claude passes the explanation it just produced so the question
    is grounded in what was actually explained — not a generic topic quiz.
    """

    explanation: str = Field(
        ...,
        description="The explanation text that was just given to the user.",
        min_length=10,
    )

    topic: str = Field(
        ...,
        description="Python topic name from ExplainConceptOutput.topic.",
    )

    key_concepts: list[str] = Field(
        ...,
        description="Key concepts from ExplainConceptOutput.key_concepts.",
    )


class GenerateCheckOutput(BaseModel):
    """
    The check question and answer signals returned to Claude.

    The signals are the most important part of this output.
    They travel with the question and are given to assess_answer later,
    so the assessment knows exactly what a correct or incorrect answer looks like.

    WHY SIGNALS INSTEAD OF A MODEL ANSWER:
      A model answer tempts the assessor to do exact matching.
      Signals describe *understanding patterns* — a correct answer might
      phrase things differently from the model, but still demonstrate the concept.
    """

    question: str = Field(
        description=(
            "Exactly one question that tests genuine understanding of the explanation. "
            "Cannot be answered by guessing or reciting the explanation verbatim. "
            "Requires the user to apply or reason about the concept."
        )
    )

    correct_signals: list[str] = Field(
        description=(
            "3–5 phrases or concepts that appear in a correct answer. "
            "e.g. for decorators: ['wraps the original function', 'returns a new function', "
            "'called at definition time not at call time']"
        )
    )

    misconception_signals: list[str] = Field(
        description=(
            "2–3 phrases that reveal a specific common misconception. "
            "e.g. 'decorators modify the function in place', 'only works on class methods'. "
            "Used to give targeted corrective feedback."
        )
    )

    hint: str = Field(
        description=(
            "A gentle hint shown if the user explicitly asks for help. "
            "Points toward the concept without giving away the answer."
        )
    )


# ═════════════════════════════════════════════════════════════════════════════
# Tool 3 — assess_answer
# ═════════════════════════════════════════════════════════════════════════════

class AssessAnswerInput(BaseModel):
    """
    Input for assessing the user's answer to the comprehension check.

    Passes the full context: original question, the signals from the check
    generator, and the user's answer. Rich context = accurate assessment.
    """

    check_question: str = Field(
        ...,
        description="The comprehension check question that was asked.",
    )

    user_answer: str = Field(
        ...,
        description="Exactly what the user typed as their answer.",
        min_length=1,
        max_length=3000,
    )

    explanation: str = Field(
        ...,
        description="The original explanation the user received, for full context.",
    )

    correct_signals: list[str] = Field(
        ...,
        description="Correct-answer signals from GenerateCheckOutput.",
    )

    misconception_signals: list[str] = Field(
        ...,
        description="Misconception signals from GenerateCheckOutput.",
    )

    topic: str = Field(
        ...,
        description="Python topic being assessed. Used in the feedback message.",
    )


class AssessAnswerOutput(BaseModel):
    """
    Assessment result returned to Claude.

    Claude uses this to decide:
      - If understood=True  → call update_skill_score, then affirm and move on.
      - If understood=False → re-explain using a different angle, then check again.
    """

    understood: bool = Field(
        description=(
            "True if the user demonstrated genuine understanding of the core concept. "
            "False if there is a significant gap or misconception."
        )
    )

    score: int = Field(
        description=(
            "Assessment score 0–100. "
            "70+ = understood. 40–69 = partial understanding. <40 = significant gap."
        ),
        ge=0,
        le=100,
    )

    feedback: str = Field(
        description=(
            "Specific, actionable feedback in coaching language. "
            "If correct: reinforce what they got right. "
            "If incorrect: name the specific misconception without being discouraging."
        )
    )

    misconception: str | None = Field(
        description=(
            "Name of the specific misconception detected, if any. "
            "e.g. 'confusing decoration with inheritance'. "
            "None if the answer is correct or the error is generic."
        )
    )

    re_explain_angle: str | None = Field(
        description=(
            "If understood=False, a suggestion for a different angle to re-explain from. "
            "e.g. 'Try using the gift-wrapping analogy', 'Show with a concrete timing example'. "
            "None if understood=True."
        )
    )


# ═════════════════════════════════════════════════════════════════════════════
# Tool 4 — update_skill_score
# ═════════════════════════════════════════════════════════════════════════════

class UpdateSkillScoreInput(BaseModel):
    """
    Input for recalculating the user's skill score for a topic.

    This tool is pure computation — no LLM involved.
    The backend calls this after receiving an AssessAnswerOutput,
    passing the current stored score alongside the assessment result.
    """

    topic: str = Field(
        ...,
        description="Python topic name. Must match the topic from ExplainConceptOutput.",
    )

    current_score: float = Field(
        ...,
        description="User's current skill score for this topic, 0–100.",
        ge=0.0,
        le=100.0,
    )

    current_attempts: int = Field(
        ...,
        description="Total number of times this topic has been assessed.",
        ge=0,
    )

    understood: bool = Field(
        ...,
        description="From AssessAnswerOutput.understood.",
    )

    assessment_score: int = Field(
        ...,
        description="From AssessAnswerOutput.score (0–100).",
        ge=0,
        le=100,
    )


class UpdateSkillScoreOutput(BaseModel):
    """
    New score and level returned to Claude and the backend.

    The backend persists `new_score` to PostgreSQL.
    Claude uses `level` and `message` to compose encouraging feedback.
    """

    topic: str

    old_score: float = Field(description="Score before this interaction.")
    new_score: float = Field(description="Score after this interaction, 0–100.")
    delta: float = Field(description="Change in score. Positive = improvement.")

    level: str = Field(
        description=(
            "Human-readable skill level: 'beginner', 'developing', 'confident', 'mastered'. "
            "Derived from new_score thresholds."
        )
    )

    message: str = Field(
        description=(
            "Coaching message about the score change. "
            "e.g. 'You're building real confidence with decorators.' "
            "Never uses grading language like 'score' or 'points'."
        )
    )

    streak_increment: bool = Field(
        description="True if this correct answer continues or starts a streak."
    )
