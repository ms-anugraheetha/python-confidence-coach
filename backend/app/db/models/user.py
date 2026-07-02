"""
app/db/models/user.py — User model.

WHY THIS TABLE EXISTS:
  Stores user identity. Every piece of learning data (conversations,
  skill scores, achievements) is foreign-keyed to a user row.

  We store only what authentication requires:
    - email      → login identifier (unique)
    - password   → hashed with bcrypt, never plaintext
    - display_name → shown in the UI (not email, for privacy)

  Profile expansions (avatar, bio) can be added as a migration later.
  YAGNI — don't build what you don't need yet.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    # These imports are only for type checking to avoid circular imports.
    # SQLAlchemy relationships use string-based references at runtime.
    from app.db.models.conversation import Conversation
    from app.db.models.skill_score import SkillScore
    from app.db.models.achievement import Achievement


class User(UUIDMixin, TimestampMixin, Base):
    """
    A registered learner.

    Relationships:
      conversations → all learning conversations
      skill_scores  → per-topic confidence scores
      achievements  → earned milestones
    """

    __tablename__ = "users"

    # ── Columns ───────────────────────────────────────────────────────────────

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,  # Fast lookup for login queries
        comment="Login identifier. Stored lowercase.",
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="bcrypt hash. Never store plaintext passwords.",
    )

    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Learner",
        comment="Name shown in the UI. Not necessarily their real name.",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    # lazy="select" (default): loaded on access — correct for async if you
    # explicitly await the query. We use selectinload() in repos for eager loading.

    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        # delete-orphan: deleting a user deletes all their conversations.
    )

    skill_scores: Mapped[list["SkillScore"]] = relationship(
        "SkillScore",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    achievements: Mapped[list["Achievement"]] = relationship(
        "Achievement",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    __table_args__ = (
        # email already has a single-column index from unique=True + index=True.
        # Add composite indexes here if needed as queries grow.
        Index("ix_users_email_lower", email, postgresql_ops={"email": "text_pattern_ops"}),
        # ^ Enables case-insensitive prefix searches on email without a function index.
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!r} email={self.email!r}>"
