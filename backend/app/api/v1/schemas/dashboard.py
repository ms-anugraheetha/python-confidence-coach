"""app/api/v1/schemas/dashboard.py — Dashboard response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SkillScoreResponse(BaseModel):
    topic: str
    score: float
    level: str
    attempts: int
    correct_streak: int
    longest_streak: int
    last_assessed_at: datetime | None

    model_config = {"from_attributes": True}


class AchievementResponse(BaseModel):
    id: uuid.UUID
    achievement_type: str
    topic: str | None
    earned_at: datetime
    metadata_json: dict[str, Any] | None

    model_config = {"from_attributes": True}


class DashboardResponse(BaseModel):
    overall_score: float
    learning_streak: int
    longest_streak: int
    topics_explored: int
    recent_achievements: list[AchievementResponse]
    mastered_concepts: list[SkillScoreResponse]
    needs_reinforcement: list[SkillScoreResponse]
    recommended_next: str | None
