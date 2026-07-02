"""
app/db/models/skill_score.py — SkillScore model.

WHY THIS TABLE EXISTS:
  One row per (user, topic) pair. Tracks how confident a user is in a
  specific Python concept over time.

  WHY UNIQUE CONSTRAINT ON (user_id, topic):
    Every user has exactly one score per topic. The unique constraint
    enforces this at the database level — you can't accidentally create
    a second "decorators" row for the same user. Upsert logic (INSERT ...
    ON CONFLICT DO UPDATE) depends on this constraint to update in place.

  WHY STORE BOTH score AND attempts SEPARATELY:
    The scoring formula uses current_attempts to compute diminishing returns:
      base_gain = max(2.0, 10.0 / (1.0 + current_attempts * 0.25))
    We need attempts to be a counter we can increment, not derive from history.

  WHY correct_streak AND longest_streak:
    correct_streak = current consecutive correct answers (resets on wrong)
    longest_streak = historical best (never decreases)
    The dashboard "learning streak" motivational feature uses longest_streak.
    Keeping both avoids recomputing from message history on every dashboard load.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class SkillScore(UUIDMixin, TimestampMixin, Base):
    """
    Per-topic confidence score for a user.

    The `score` column is driven by the pure-math `update_skill_score`
    MCP tool — no LLM involved in the calculation.

    Score levels:
      0–49   → beginner
      50–74  → developing
      75–89  → confident
      90–100 → mastered
    """

    __tablename__ = "skill_scores"

    # ── Columns ───────────────────────────────────────────────────────────────

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    topic: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="The Python concept. e.g. 'decorators', 'list comprehensions', 'async/await'.",
    )

    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Confidence score 0.0–100.0. Updated by update_skill_score tool.",
    )

    level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="beginner",
        comment="Derived label: beginner | developing | confident | mastered.",
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment=(
            "Total comprehension check attempts for this topic. "
            "Used in the diminishing-returns formula. "
            "Incremented on every check, regardless of outcome."
        ),
    )

    correct_streak: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Current consecutive correct answers. Resets to 0 on any wrong answer.",
    )

    longest_streak: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Historical best streak for this topic. Never decreases.",
    )

    last_assessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of the most recent comprehension check attempt. Null until first check.",
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    user: Mapped["User"] = relationship(
        "User",
        back_populates="skill_scores",
    )

    # ── Constraints & Indexes ─────────────────────────────────────────────────
    __table_args__ = (
        # Enforces one score row per (user, topic).
        # Also the target of INSERT ... ON CONFLICT (user_id, topic) DO UPDATE.
        UniqueConstraint("user_id", "topic", name="uq_skill_scores_user_topic"),

        # Dashboard query: "all topics for user X, sorted by score (mastered first)"
        Index("ix_skill_scores_user_score", "user_id", "score"),
    )

    def __repr__(self) -> str:
        return (
            f"<SkillScore user_id={self.user_id!r} topic={self.topic!r} "
            f"score={self.score!r} level={self.level!r}>"
        )
