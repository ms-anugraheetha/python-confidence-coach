"""
app/db/models/__init__.py — Model registry.

WHY THIS FILE EXISTS:
  Alembic's env.py does `from app.db.models import *` (or imports Base)
  to discover all models before generating migrations. If a model module
  is never imported, its table won't appear in the migration diff.

  By importing all models here, any file that imports from this package
  (including Alembic's env.py) automatically registers every table with
  SQLAlchemy's MetaData — no manual tracking required.

  Import order doesn't matter for SQLAlchemy — it resolves FK references
  lazily at mapper configuration time. But keeping them alphabetical
  makes diffs clean.
"""

from app.db.models.achievement import Achievement
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.models.skill_score import SkillScore
from app.db.models.user import User

__all__ = [
    "Achievement",
    "Conversation",
    "Message",
    "SkillScore",
    "User",
]
