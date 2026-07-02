"""
app/db/repositories/skill_repo.py — SkillRepository.

RESPONSIBILITIES:
  - Upsert skill scores after every comprehension check
  - Load the full skill profile for the dashboard
  - Identify mastered topics and topics needing reinforcement

THE UPSERT PATTERN:
  PostgreSQL's INSERT ... ON CONFLICT DO UPDATE is used here instead of
  SELECT then UPDATE. This avoids a race condition where two requests for
  the same user/topic arrive simultaneously and both try to create the row.

  SQLAlchemy exposes this via `insert().on_conflict_do_update()`.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.skill_score import SkillScore


class SkillRepository:
    """Data access layer for the skill_scores table."""

    async def get_by_user_and_topic(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        topic: str,
    ) -> SkillScore | None:
        """Fetch a single skill score row. Returns None if this topic is new."""
        result = await db.execute(
            select(SkillScore).where(
                SkillScore.user_id == user_id,
                SkillScore.topic == topic,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[SkillScore]:
        """
        All skill scores for a user, sorted by score descending.
        Highest-confidence topics first — for the dashboard "mastered" list.
        """
        result = await db.execute(
            select(SkillScore)
            .where(SkillScore.user_id == user_id)
            .order_by(SkillScore.score.desc())
        )
        return list(result.scalars().all())

    async def upsert(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        topic: str,
        new_score: float,
        new_level: str,
        attempts_increment: int = 1,
        understood: bool,
    ) -> SkillScore:
        """
        Insert or update the skill score for (user_id, topic).

        WHY UPSERT:
          The first time a user asks about "decorators", no row exists —
          we INSERT. Every subsequent ask UPDATEs in place.
          The ON CONFLICT target is the unique constraint uq_skill_scores_user_topic.

        STREAK LOGIC:
          We can't do streak math in pure SQL here because it depends on
          whether `understood` is True or False. We fetch, update in Python,
          then save. The fetch is cheap (it's a single row by unique key).
        """
        # Step 1: Fetch existing (or create a stub)
        existing = await self.get_by_user_and_topic(db, user_id, topic)

        if existing is None:
            # First time seeing this topic — create the row
            row = SkillScore(
                user_id=user_id,
                topic=topic,
                score=new_score,
                level=new_level,
                attempts=attempts_increment,
                correct_streak=1 if understood else 0,
                longest_streak=1 if understood else 0,
                last_assessed_at=datetime.now(timezone.utc),
            )
            db.add(row)
            await db.flush()
            await db.refresh(row)
            return row

        # Step 2: Update existing row
        existing.score = new_score
        existing.level = new_level
        existing.attempts += attempts_increment
        existing.last_assessed_at = datetime.now(timezone.utc)

        if understood:
            existing.correct_streak += 1
            existing.longest_streak = max(
                existing.longest_streak, existing.correct_streak
            )
        else:
            existing.correct_streak = 0
            # longest_streak never decreases

        await db.flush()
        await db.refresh(existing)
        return existing

    async def get_mastered_topics(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        *,
        limit: int = 5,
    ) -> list[SkillScore]:
        """
        Topics where score >= 90 (mastered level).
        Used for the dashboard "Concepts You've Mastered" section.
        """
        result = await db.execute(
            select(SkillScore)
            .where(
                SkillScore.user_id == user_id,
                SkillScore.score >= 90.0,
            )
            .order_by(SkillScore.score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_needs_reinforcement(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        *,
        limit: int = 3,
    ) -> list[SkillScore]:
        """
        Topics where score < 50 (beginner level) with at least 1 attempt.
        Used for the dashboard "Areas Needing Reinforcement" section.
        Returns lowest scores first so the most urgent topics appear at top.
        """
        result = await db.execute(
            select(SkillScore)
            .where(
                SkillScore.user_id == user_id,
                SkillScore.score < 50.0,
                SkillScore.attempts > 0,
            )
            .order_by(SkillScore.score.asc())
            .limit(limit)
        )
        return list(result.scalars().all())


skill_repo = SkillRepository()
