"""
app/services/chat_service.py — Coaching loop via the MCP server.

Delegates all AI work to the four MCP tools (explain_concept,
generate_comprehension_check, assess_answer, update_skill_score) through
mcp_client. This service only orchestrates the flow and persists results —
it never calls an LLM directly.

FLOW:
  New question   → explain_concept → generate_comprehension_check
  Check answer   → assess_answer → (True) update_skill_score
                                  → (False) explain_concept (new angle) → generate_comprehension_check
"""

from __future__ import annotations

import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.message import Message
from app.db.repositories.conversation_repo import conversation_repo
from app.db.repositories.message_repo import message_repo
from app.db.repositories.skill_repo import skill_repo
from app.services.mcp_client import mcp_client

logger = get_logger(__name__)


def _extract_code(content: str) -> tuple[str, str | None]:
    pattern = r"```[a-zA-Z]*\n?([\s\S]*?)```"
    match = re.search(pattern, content)
    if not match:
        return content.strip(), None
    code = match.group(1).strip()
    question = re.sub(pattern, "", content).strip() or "What does this code do?"
    return question, code


def _get_last_check(messages: list[Message]) -> dict | None:
    for msg in reversed(messages):
        if msg.role == "assistant" and msg.tool_calls_json:
            if msg.tool_calls_json.get("check_question"):
                return msg.tool_calls_json
    return None


def _is_new_question(content: str) -> bool:
    s = content.strip()
    if "```" in s or len(s) > 300:
        return True
    if s.endswith("?") and len(s) < 80:
        return True
    return False


async def handle_message(
    db: AsyncSession,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    content: str,
) -> tuple[Message, Message]:
    # Save user message
    user_msg = await message_repo.create(
        db, conversation_id=conversation_id, role="user", content=content
    )

    # Get recent history to detect context
    recent = await message_repo.get_recent_for_conversation(db, conversation_id, limit=10)
    last_check = _get_last_check(recent)

    if last_check and not _is_new_question(content):
        assistant_msg = await _handle_check_answer(
            db, conversation_id, user_id, content, last_check
        )
    else:
        assistant_msg = await _handle_new_question(db, conversation_id, content)

    # Update conversation title + timestamp
    convo = await conversation_repo.get_by_id(db, conversation_id)
    if convo:
        if not convo.title:
            title = content[:100].strip() + ("…" if len(content) > 100 else "")
            await conversation_repo.set_title(db, convo, title)
        await conversation_repo.touch(db, convo)

    return user_msg, assistant_msg


async def _explain_and_check(question: str, code: str | None = None) -> dict:
    """
    Call explain_concept then generate_comprehension_check, and assemble
    everything the next turn needs into one dict (this becomes tool_calls_json).
    """
    explanation_result = await mcp_client.explain_concept(question=question, code=code)

    explanation: str = explanation_result.get("explanation", "")
    topic: str = explanation_result.get("topic", "python")
    key_concepts: list[str] = explanation_result.get("key_concepts", [])

    check_result = await mcp_client.generate_comprehension_check(
        explanation=explanation,
        topic=topic,
        key_concepts=key_concepts,
    )

    return {
        "explanation": explanation,
        "topic": topic,
        "key_concepts": key_concepts,
        "code_example": explanation_result.get("code_example"),
        "analogy": explanation_result.get("analogy"),
        "check_question": check_result.get("question", "Can you summarize what you learned?"),
        "correct_signals": check_result.get("correct_signals", []),
        "misconception_signals": check_result.get("misconception_signals", []),
        "hint": check_result.get("hint"),
    }


async def _handle_new_question(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    content: str,
) -> Message:
    question, code = _extract_code(content)
    logger.info("chat_new_question", question=question[:60])

    result = await _explain_and_check(question, code)

    full_content = f"{result['explanation']}\n\n**Quick check:** {result['check_question']}"

    return await message_repo.create(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=full_content,
        topic_detected=result["topic"],
        tool_calls_json=result,
    )


async def _handle_check_answer(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    user_answer: str,
    check_meta: dict,
) -> Message:
    topic = check_meta.get("topic", "python")
    check_question = check_meta.get("check_question", "")
    explanation = check_meta.get("explanation", "")
    correct_signals = check_meta.get("correct_signals", [])
    misconception_signals = check_meta.get("misconception_signals", [])
    logger.info("chat_check_answer", topic=topic)

    assessment = await mcp_client.assess_answer(
        check_question=check_question,
        user_answer=user_answer,
        explanation=explanation,
        correct_signals=correct_signals,
        misconception_signals=misconception_signals,
        topic=topic,
    )
    understood: bool = assessment.get("understood", False)
    feedback: str = assessment.get("feedback", "Good effort!")
    assessment_score: int = assessment.get("score", 50)

    if understood:
        # Fetch current skill state and let the MCP tool compute the new score.
        skill = await skill_repo.get_by_user_and_topic(db, user_id, topic)
        current_score: float = skill.score if skill else 0.0
        current_attempts: int = skill.attempts if skill else 0

        score_result = await mcp_client.update_skill_score(
            topic=topic,
            current_score=current_score,
            current_attempts=current_attempts,
            understood=True,
            assessment_score=assessment_score,
        )

        updated = await skill_repo.upsert(
            db,
            user_id=user_id,
            topic=topic,
            new_score=score_result.get("new_score", current_score),
            new_level=score_result.get("level", "beginner"),
            attempts_increment=1,
            understood=True,
        )

        coaching_message = score_result.get("message", "")
        reply = (
            f"✅ {feedback}\n\n"
            f"{coaching_message}\n\n"
            f"You're now at **{updated.level}** level for {topic} "
            f"(score: {updated.score:.0f}/100). "
            f"What would you like to explore next?"
        )
        tool_json: dict = {"check_question": None, "topic": topic}

    else:
        # Fetch skill to track the failed attempt (no score change on a miss).
        skill = await skill_repo.get_by_user_and_topic(db, user_id, topic)
        current_score = skill.score if skill else 0.0
        current_level = skill.level if skill else "beginner"

        await skill_repo.upsert(
            db,
            user_id=user_id,
            topic=topic,
            new_score=current_score,
            new_level=current_level,
            attempts_increment=1,
            understood=False,
        )

        # Re-explain from the angle assess_answer suggested.
        re_explain_angle = assessment.get("re_explain_angle")
        re_explain_prompt = (
            f"Re-explain '{topic}' in a simpler way for a beginner who is still confused. "
            + (f"Try this angle: {re_explain_angle}." if re_explain_angle
               else "Use a different analogy or example than before.")
        )
        result = await _explain_and_check(re_explain_prompt)

        reply = (
            f"No worries, let me try a different angle!\n\n"
            f"{feedback}\n\n"
            f"{result['explanation']}\n\n"
            f"**Quick check:** {result['check_question']}"
        )
        tool_json = result
        topic = result["topic"]

    return await message_repo.create(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=reply,
        topic_detected=topic,
        tool_calls_json=tool_json,
    )
