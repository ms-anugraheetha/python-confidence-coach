"""
app/db/models/achievement.py — Achievement model.

WHY THIS TABLE EXISTS:
  Stores milestone badges earned by the user. These are discrete events
  ("first concept mastered", "5-day streak") rather than continuous scores.

  WHY UNIQUE ON (user_id, achievement_type, topic):
    An achievement should only be earned once. The unique constraint prevents
    duplicate inserts at the DB level. `topic` is included because some
    achievements are topic-specific ("mastered decorators") and others are
    global (topic=NULL, e.g., "7-day streak").

    NULL is allowed in `topic` to support global achievements. Note: in
    PostgreSQL, two rows with the same (user_id, achievement_type, NULL)
    would NOT be blocked by a standard UNIQUE constraint because NULL != NULL.
    We handle this in the repository with a partial index or explicit check
    before insert.

  WHY JSONB metadata:
    Different achievement types carry different payloads. A "streak" badge
    carries {"streak_length": 7}. A "mastered_topic" badge carries
    {"topic": "decorators", "final_score": 94.5}. JSONB keeps this flexible
    without requiring a new column per achievement type.

  ACHIEVEMENT TYPES (not enforced at DB level, enforced in repo):
    "first_concept"     — explained and checked a concept for the first time
    "topic_mastered"    — score reached 90+ on a topic
    "streak_3"          — 3 consecutive correct answers on any topic
    "streak_7"          — 7 consecutive correct answers
    "topic_milestone_5" — learned 5 distinct topics
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class Achievement(UUIDMixin, TimestampMixin, Base):
    """
    A milestone badge earned by a user.

    Earned achievements are immutable records — never updated, only created.
    The `earned_at` column records the exact moment the milestone was hit.
    """

    __tablename__ = "achievements"

    # ── Columns ───────────────────────────────────────────────────────────────

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    achievement_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Category key. e.g. 'topic_mastered', 'streak_7'. Validated in repo layer.",
    )

    topic: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment=(
            "Topic this achievement is for. "
            "NULL for global achievements like streak badges."
        ),
    )

    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When the milestone was hit. Immutable after creation.",
    )

    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment=(
            "Achievement-specific data. "
            "e.g. {'final_score': 94.5} for topic_mastered, "
            "{'streak_length': 7} for streak badges."
        ),
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    user: Mapped["User"] = relationship(
        "User",
        back_populates="achievements",
    )

    # ── Constraints & Indexes ─────────────────────────────────────────────────
    __table_args__ = (
        # Prevents duplicate badges for topic-specific achievements.
        # Note: does NOT cover global (topic=NULL) achievements due to NULL!=NULL.
        # Those are guarded in the AchievementRepository before insert.
        UniqueConstraint(
            "user_id", "achievement_type", "topic",
            name="uq_achievements_user_type_topic",
        ),

        # Dashboard: "all achievements for user X, newest first"
        Index("ix_achievements_user_earned", "user_id", "earned_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Achievement user_id={self.user_id!r} type={self.achievement_type!r} "
            f"topic={self.topic!r}>"
        )
