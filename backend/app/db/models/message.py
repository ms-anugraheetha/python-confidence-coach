"""
app/db/models/message.py — Message model.

WHY THIS TABLE EXISTS:
  Stores every exchange in a conversation — user questions, AI explanations,
  and the MCP tool call data that produced them.

  WHY JSONB FOR tool_calls_json:
    Tool call data (what Claude called, with what args, what it returned)
    is variable-length and variable-schema. Different tools return different
    structures. JSONB stores this without requiring a fixed schema, while
    still being indexable and queryable if needed.

  WHY STORE topic_detected FLAT:
    The explain_concept tool returns the detected topic ("decorators").
    Storing it flat on the message means we can query "all messages about
    decorators" without parsing JSONB on every row. It also feeds the
    skill_score update directly.

  ROLES:
    "user"      → the learner's message
    "assistant" → the coach's full response (explanation + check question)
    "tool"      → raw tool result (internal, not shown in UI)
"""

from __future__ import annotations

import uuid
from typing import Any, TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.conversation import Conversation


class Message(UUIDMixin, TimestampMixin, Base):
    """
    A single message in a conversation.

    Both user and assistant messages are stored here.
    The `role` column distinguishes who sent each message.
    Tool call data is stored as JSONB for full auditability.
    """

    __tablename__ = "messages"

    # ── Columns ───────────────────────────────────────────────────────────────

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="'user' | 'assistant' | 'tool'. Mirrors Claude's message roles.",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The text content shown to the user. For tool messages, this is the tool result.",
    )

    topic_detected: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment=(
            "Python topic detected by explain_concept tool. "
            "e.g. 'decorators'. Null for user messages. "
            "Stored flat for efficient per-topic queries."
        ),
    )

    tool_calls_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment=(
            "Raw MCP tool call data. Structure: "
            "{'calls': [{'tool': str, 'input': dict, 'output': dict, 'duration_ms': int}]}. "
            "Null for user messages. Used for debugging and audit."
        ),
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    __table_args__ = (
        # "All messages in conversation X, in order" — the most common query.
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),

        # "All messages about topic X for user Y" — powers topic review feature.
        Index("ix_messages_topic", "topic_detected"),
    )

    def __repr__(self) -> str:
        preview = self.content[:40] if self.content else ""
        return f"<Message id={self.id!r} role={self.role!r} content={preview!r}>"
