"""
tools/skill.py — update_skill_score MCP tool.

WHAT THIS TOOL DOES:
  Pure computation — no LLM call involved.
  Applies the confidence scoring algorithm and returns the new score,
  level, and a coaching message. The backend persists the new score
  to PostgreSQL after receiving this result.

SCORING ALGORITHM:
  On correct answer (understood=True):
    - Gain uses diminishing returns: max(2.0, 10.0 / (1 + attempts * 0.25))
    - Early answers are worth more — each gain shrinks as attempts grow.
    - This means you can't rush to "mastered" in a few lucky answers.

  On incorrect answer (understood=False):
    - No score change. The tool is only called when understood=True.
    - This function validates this precondition and logs a warning if violated.

SKILL LEVELS:
  0–49:  beginner     (just starting out)
  50–74: developing   (building understanding)
  75–89: confident    (solid grasp)
  90–100: mastered    (deep, reliable understanding)

WHY NO PENALTY FOR WRONG ANSWERS:
  Failed comprehension checks are part of learning, not evidence of regression.
  Penalising them would discourage engagement — learners would stop trying.
  The loop continues until they understand; that's the feature, not the failure.
"""

from __future__ import annotations

import logging

from models.schemas import UpdateSkillScoreInput, UpdateSkillScoreOutput

logger = logging.getLogger(__name__)

# Skill level thresholds
_THRESHOLDS = {
    "mastered":   90.0,
    "confident":  75.0,
    "developing": 50.0,
    # below 50 = "beginner"
}

# Coaching messages keyed by level transition
_LEVEL_MESSAGES = {
    "mastered": "You've built deep, reliable confidence with {topic}. Impressive.",
    "confident": "You have a solid grasp of {topic} now. Keep building on this.",
    "developing": "You're making real progress with {topic}. Each answer strengthens it.",
    "beginner": "You're getting started with {topic}. Every question builds the foundation.",
}

# Messages for score increases of different magnitudes
_GAIN_MESSAGES = {
    "large": "Nice — that understanding is really taking hold.",
    "medium": "Good — you're strengthening your grasp of this.",
    "small": "You've got a solid handle on this already. Still getting stronger.",
}


async def update_skill_score(
    topic: str,
    current_score: float,
    current_attempts: int,
    understood: bool,
    assessment_score: int,
) -> dict:
    """
    Calculate the new skill score after a comprehension check result.

    This tool is called ONLY when understood=True. The system prompt
    enforces this — Claude calls this after a confirmed correct answer.

    Args:
        topic:            Python topic name e.g. "decorators".
        current_score:    User's current score for this topic (0–100).
        current_attempts: Total assessments completed for this topic.
        understood:       Must be True. Tool logs a warning if False.
        assessment_score: Raw assessment score 0–100 from assess_answer.

    Returns:
        UpdateSkillScoreOutput as a dict with new score, level, delta, message.
    """
    validated = UpdateSkillScoreInput(
        topic=topic,
        current_score=current_score,
        current_attempts=current_attempts,
        understood=understood,
        assessment_score=assessment_score,
    )

    if not validated.understood:
        # This shouldn't happen — the system prompt prevents it.
        # Log and return no-change if it does.
        logger.warning(
            "update_skill_score called with understood=False — no change applied",
            topic=validated.topic,
            current_score=validated.current_score,
        )
        return UpdateSkillScoreOutput(
            topic=validated.topic,
            old_score=round(validated.current_score, 1),
            new_score=round(validated.current_score, 1),
            delta=0.0,
            level=_score_to_level(validated.current_score),
            message="Keep going — understanding comes with practice.",
            streak_increment=False,
        ).model_dump()

    old_score = validated.current_score

    # ── Scoring algorithm ────────────────────────────────────────────────────
    #
    # Base gain uses diminishing returns as attempts increase:
    #   attempts=0:  gain ≈ 10.0
    #   attempts=4:  gain ≈ 6.7
    #   attempts=10: gain ≈ 4.4
    #   attempts=20: gain ≈ 2.9
    #
    # Then we scale the gain by how well they did in the assessment.
    # A score of 100 gets full gain. A score of 70 gets 70% of the gain.
    # Minimum gain of 1.0 regardless of score (progress is always made).
    #
    base_gain = max(2.0, 10.0 / (1.0 + validated.current_attempts * 0.25))
    quality_multiplier = max(0.5, validated.assessment_score / 100.0)
    gain = round(base_gain * quality_multiplier, 2)

    new_score = round(min(100.0, old_score + gain), 1)
    delta = round(new_score - old_score, 1)

    new_level = _score_to_level(new_score)
    old_level = _score_to_level(old_score)
    level_up = new_level != old_level and _level_rank(new_level) > _level_rank(old_level)

    # Build message
    if level_up:
        message = f"🎯 You've reached '{new_level}' with {validated.topic}! " + _LEVEL_MESSAGES[new_level].format(topic=validated.topic)
    else:
        gain_tier = "large" if delta >= 6 else "medium" if delta >= 3 else "small"
        message = _GAIN_MESSAGES[gain_tier]

    logger.info(
        "update_skill_score applied",
        topic=validated.topic,
        old_score=old_score,
        new_score=new_score,
        delta=delta,
        level=new_level,
        level_up=level_up,
    )

    return UpdateSkillScoreOutput(
        topic=validated.topic,
        old_score=round(old_score, 1),
        new_score=new_score,
        delta=delta,
        level=new_level,
        message=message,
        streak_increment=True,  # Any understood=True answer increments the streak.
    ).model_dump()


def _score_to_level(score: float) -> str:
    """Map a numeric score to its skill level label."""
    if score >= _THRESHOLDS["mastered"]:
        return "mastered"
    if score >= _THRESHOLDS["confident"]:
        return "confident"
    if score >= _THRESHOLDS["developing"]:
        return "developing"
    return "beginner"


def _level_rank(level: str) -> int:
    """Numeric rank for comparing levels."""
    return {"beginner": 0, "developing": 1, "confident": 2, "mastered": 3}.get(level, 0)
