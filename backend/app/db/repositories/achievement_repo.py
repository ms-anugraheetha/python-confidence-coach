"""
app/db/repositories/achievement_repo.py — AchievementRepository.

RESPONSIBILITIES:
  - Award achievements (safely, no duplicates)
  - List recent achievements for the dashboard

THE NULL UNIQUENESS PROBLEM:
  In PostgreSQL, NULL != NULL in unique constraints. Two rows with
  (user_id='x', achievement_type='streak_7', topic=NULL) would both
  satisfy the unique constraint on (user_id, achievement_type, topic)
  because the DB treats each NULL as distinct.

  We guard against this in award() with an explicit SELECT before INSERT:
  if a matching row already exists (including topic=None check), we return
  the existing row rather than creating a duplicate.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.achievement import Achievement


class AchievementRepository:
    """Data access layer for the achievements table."""

    async def exists(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        achievement_type: str,
        topic: str | None = None,
    ) -> bool:
        """
        Check if the user already has this achievement.

        Handles the NULL topic case explicitly so we don't accidentally
        award a global badge twice (which the DB unique constraint wouldn't catch).
        """
        if topic is None:
            query = select(Achievement.id).where(
                Achievement.user_id == user_id,
                Achievement.achievement_type == achievement_type,
                Achievement.topic.is_(None),
            )
        else:
            query = select(Achievement.id).where(
                Achievement.user_id == user_id,
                Achievement.achievement_type == achievement_type,
                Achievement.topic == topic,
            )

        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    async def award(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        achievement_type: str,
        topic: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> Achievement | None:
        """
        Award an achievement if the user doesn't already have it.

        Returns the new Achievement if it was just created.
        Returns None if the user already has this achievement (idempotent).

        WHY RETURN None ON DUPLICATE:
          The calling service can check "was this just earned?" to decide
          whether to include a "You earned a badge!" notification in the response.
          A None return means "already had it, nothing to show."
        """
        already_earned = await self.exists(db, user_id, achievement_type, topic)
        if already_earned:
            return None

        badge = Achievement(
            user_id=user_id,
            achievement_type=achievement_type,
            topic=topic,
            metadata_json=metadata_json,
        )
        db.add(badge)
        await db.flush()
        await db.refresh(badge)
        return badge

    async def list_recent_for_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        *,
        limit: int = 5,
    ) -> list[Achievement]:
        """
        Most recently earned achievements for the dashboard.
        Newest first.
        """
        result = await db.execute(
            select(Achievement)
            .where(Achievement.user_id == user_id)
            .order_by(Achievement.earned_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_for_user(self, db: AsyncSession, user_id: uuid.UUID) -> int:
        """
        Total badge count. Used for "milestone_5" style checks.
        e.g., award "topic_milestone_5" when count reaches 5.
        """
        from sqlalchemy import func
        result = await db.execute(
            select(func.count(Achievement.id)).where(Achievement.user_id == user_id)
        )
        return result.scalar_one() or 0


achievement_repo = AchievementRepository()
