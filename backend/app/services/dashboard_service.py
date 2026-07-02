"""
app/services/dashboard_service.py — Aggregate dashboard data.

Queries skill_scores + achievements and assembles the DashboardData
payload the frontend sidebar needs in one request.

OVERALL SCORE:
  Weighted average of all topic scores, weighted by attempts.
  Topics the user has practiced more contribute more to their overall score.
  A user who has mastered one topic and barely touched three others
  won't show 90+ overall — the average stays honest.

RECOMMENDED NEXT:
  The topic with the most attempts that is still below 75 (not yet confident).
  "Most attempts" = the learner is already engaged with it.
  Recommending what they've already started is more motivating than suggesting
  something completely new.

LEARNING STREAK:
  Currently derived from skill_scores.last_assessed_at patterns.
  Phase 7 can add a dedicated daily_activity table if streak precision matters.
  For now: count distinct days with at least one assessment in the last 30 days.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.achievement_repo import achievement_repo
from app.db.repositories.skill_repo import skill_repo


async def get_dashboard(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """
    Assemble the full dashboard payload.
    Called by GET /api/v1/dashboard.
    """
    all_skills = await skill_repo.list_for_user(db, user_id)
    mastered = await skill_repo.get_mastered_topics(db, user_id, limit=5)
    needs_work = await skill_repo.get_needs_reinforcement(db, user_id, limit=3)
    recent_achievements = await achievement_repo.list_recent_for_user(db, user_id, limit=5)

    # Overall score — attempts-weighted average
    overall_score = _compute_overall_score(all_skills)

    # Learning streak
    learning_streak, longest_streak = _compute_streaks(all_skills)

    # Recommended next
    recommended_next = _recommend_next(all_skills)

    return {
        "overall_score": overall_score,
        "learning_streak": learning_streak,
        "longest_streak": longest_streak,
        "topics_explored": len(all_skills),
        "recent_achievements": recent_achievements,
        "mastered_concepts": mastered,
        "needs_reinforcement": needs_work,
        "recommended_next": recommended_next,
    }


def _compute_overall_score(skills) -> float:
    """Attempts-weighted average of all topic scores."""
    if not skills:
        return 0.0
    total_weight = sum(max(1, s.attempts) for s in skills)
    weighted_sum = sum(s.score * max(1, s.attempts) for s in skills)
    return round(weighted_sum / total_weight, 1)


def _compute_streaks(skills) -> tuple[int, int]:
    """
    Derive learning streak from assessment dates.

    Counts consecutive days (going backwards from today) on which at
    least one topic was assessed. Returns (current_streak, longest_streak).
    The longest_streak here is derived from the individual topic longest_streaks
    until a dedicated activity log is added in a future phase.
    """
    # Collect all last_assessed_at timestamps
    dates: set[str] = set()
    for s in skills:
        if s.last_assessed_at:
            dates.add(s.last_assessed_at.date().isoformat())

    today = datetime.now(timezone.utc).date()
    streak = 0
    check_date = today

    while check_date.isoformat() in dates:
        streak += 1
        check_date = check_date - timedelta(days=1)

    longest = max((s.longest_streak for s in skills), default=0)
    return streak, longest


def _recommend_next(skills) -> str | None:
    """
    Recommend the topic with the most attempts that is still below 75.
    Returns None if all topics are at confident/mastered level.
    """
    candidates = [s for s in skills if s.score < 75.0 and s.attempts > 0]
    if not candidates:
        return None
    # Sort by attempts desc (most engaged with first)
    candidates.sort(key=lambda s: s.attempts, reverse=True)
    return candidates[0].topic
