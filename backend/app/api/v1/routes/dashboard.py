"""
app/api/v1/routes/dashboard.py — Dashboard data endpoint.

ROUTES:
  GET /api/v1/dashboard — return all dashboard data in one request
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.dashboard import (
    AchievementResponse,
    DashboardResponse,
    SkillScoreResponse,
)
from app.core.security import get_current_user_id
from app.db.session import get_db
from app.services.dashboard_service import get_dashboard

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardResponse:
    """
    Return the full Python Skill Dashboard payload.

    Aggregates: overall score, streaks, achievements, mastered topics,
    topics needing reinforcement, and recommended next topic.

    The frontend calls this once on load and again after each AI response
    (via the refreshTrigger counter in CoachPage).
    """
    data = await get_dashboard(db, user_id)

    return DashboardResponse(
        overall_score=data["overall_score"],
        learning_streak=data["learning_streak"],
        longest_streak=data["longest_streak"],
        topics_explored=data["topics_explored"],
        recent_achievements=[
            AchievementResponse.model_validate(a)
            for a in data["recent_achievements"]
        ],
        mastered_concepts=[
            SkillScoreResponse.model_validate(s)
            for s in data["mastered_concepts"]
        ],
        needs_reinforcement=[
            SkillScoreResponse.model_validate(s)
            for s in data["needs_reinforcement"]
        ],
        recommended_next=data["recommended_next"],
    )
