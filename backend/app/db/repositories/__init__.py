"""
app/db/repositories/__init__.py — Repository registry.

Import all singleton repo instances here for convenient access:

  from app.db.repositories import user_repo, conversation_repo

Using module-level singletons (one instance per process) is safe because
repositories carry NO state — they're just method containers over a session.
The session itself is per-request and passed as an argument.
"""

from app.db.repositories.achievement_repo import achievement_repo, AchievementRepository
from app.db.repositories.conversation_repo import conversation_repo, ConversationRepository
from app.db.repositories.message_repo import message_repo, MessageRepository
from app.db.repositories.skill_repo import skill_repo, SkillRepository
from app.db.repositories.user_repo import user_repo, UserRepository

__all__ = [
    "achievement_repo",
    "AchievementRepository",
    "conversation_repo",
    "ConversationRepository",
    "message_repo",
    "MessageRepository",
    "skill_repo",
    "SkillRepository",
    "user_repo",
    "UserRepository",
]
