"""
app/db/repositories/message_repo.py — MessageRepository.

RESPONSIBILITIES:
  - Append user and assistant messages to a conversation
  - Load the last N messages (context window for the next Claude call)
  - Store tool call audit data

IMPORTANT:
  After saving an assistant message, callers should also call
  conversation_repo.touch(db, conversation) to update last_message_at.
  The message repo doesn't do this itself — single responsibility.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.message import Message


class MessageRepository:
    """Data access layer for the messages table."""

    async def create(
        self,
        db: AsyncSession,
        *,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        topic_detected: str | None = None,
        tool_calls_json: dict[str, Any] | None = None,
    ) -> Message:
        """
        Append a message to a conversation.

        `role` must be one of: "user", "assistant", "tool"
        `topic_detected` is set by the backend after the explain_concept
          tool responds — it's None for user messages.
        `tool_calls_json` holds the raw MCP call data for assistant messages.
        """
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            topic_detected=topic_detected,
            tool_calls_json=tool_calls_json,
        )
        db.add(msg)
        await db.flush()
        await db.refresh(msg)
        return msg

    async def get_recent_for_conversation(
        self,
        db: AsyncSession,
        conversation_id: uuid.UUID,
        *,
        limit: int = 20,
    ) -> list[Message]:
        """
        Fetch the N most recent messages, returned in chronological order.

        Used to build the message history array for Claude API calls.
        `limit=20` keeps the context window from growing unboundedly.

        Note the subquery trick: we sort DESC to get the *last* N rows,
        then wrap in a subquery and sort ASC to return them chronologically.
        This avoids loading the entire history just to grab the tail.
        """
        subquery = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .subquery()
        )
        # Alias to query the subquery in correct order
        from sqlalchemy.orm import aliased
        msg_alias = aliased(Message, subquery)

        result = await db.execute(
            select(msg_alias).order_by(msg_alias.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_for_conversation(
        self,
        db: AsyncSession,
        conversation_id: uuid.UUID,
    ) -> list[Message]:
        """
        All messages in a conversation, chronological order.

        Used for full chat history display (when loading a past conversation).
        For Claude API context, use get_recent_for_conversation with a limit.
        """
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())


message_repo = MessageRepository()
