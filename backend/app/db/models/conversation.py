"""
app/db/models/conversation.py — Conversation model.

WHY THIS TABLE EXISTS:
  Groups a sequence of messages into a named session.
  One user has many conversations. The dashboard shows recent conversations
  so users can continue where they left off.

  WHY DENORMALIZE last_message_at:
    Sorting conversations by recency is a very common dashboard query.
    Deriving it from MAX(messages.created_at) requires a subquery or join
    on every dashboard load. Storing it flat is a deliberate trade-off:
    one extra UPDATE per message in exchange for a simple ORDER BY.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.message import Message


class Conversation(UUIDMixin, TimestampMixin, Base):
    """
    A learning session — a sequence of messages between a user and the coach.

    Relationships:
      user     → the learner this conversation belongs to
      messages → all exchanges in this session, ordered by created_at
    """

    __tablename__ = "conversations"

    # ── Columns ───────────────────────────────────────────────────────────────

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The user this conversation belongs to.",
    )

    title: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment=(
            "Auto-generated from the first user message. "
            "e.g. 'How do decorators work?' "
            "Null until the first message is saved."
        ),
    )

    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Denormalized for efficient 'recent conversations' sorting.",
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    user: Mapped["User"] = relationship(
        "User",
        back_populates="conversations",
    )

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
        # Messages are always retrieved in chronological order.
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    __table_args__ = (
        # Dashboard query: "latest conversations for user X, sorted by recency"
        Index("ix_conversations_user_last_msg", "user_id", "last_message_at"),
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id!r} user_id={self.user_id!r} title={self.title!r}>"
