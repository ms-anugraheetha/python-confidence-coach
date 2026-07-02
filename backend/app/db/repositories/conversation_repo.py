"""
app/db/repositories/conversation_repo.py — ConversationRepository.

RESPONSIBILITIES:
  - Create conversations (one per chat session the user starts)
  - Load conversations for the sidebar (recent list)
  - Fetch a single conversation with all its messages (chat load)
  - Update the denormalized last_message_at on every new message
  - Set the auto-generated title (derived from first user message)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.conversation import Conversation


class ConversationRepository:
    """Data access layer for the conversations table."""

    async def create(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        title: str | None = None,
    ) -> Conversation:
        """
        Start a new conversation.

        `title` is usually None at creation time — the first user message
        hasn't been sent yet. It gets filled in by `set_title()` after the
        first message is saved.
        """
        convo = Conversation(user_id=user_id, title=title)
        db.add(convo)
        await db.flush()
        await db.refresh(convo)
        return convo

    async def get_by_id(
        self,
        db: AsyncSession,
        conversation_id: uuid.UUID,
        *,
        with_messages: bool = False,
    ) -> Conversation | None:
        """
        Fetch a conversation by ID.

        with_messages=True: eagerly loads all messages in chronological order.
        Used when loading the full chat history for display.

        with_messages=False (default): loads just the conversation row.
        Used for ownership checks and metadata updates.
        """
        query = select(Conversation).where(Conversation.id == conversation_id)

        if with_messages:
            query = query.options(selectinload(Conversation.messages))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Conversation]:
        """
        Recent conversations for the sidebar, newest first.

        Uses the denormalized last_message_at index — O(log n) on the composite
        index rather than a subquery join on messages.
        """
        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.last_message_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def set_title(
        self,
        db: AsyncSession,
        conversation: Conversation,
        title: str,
    ) -> Conversation:
        """
        Set the conversation title from the first user message.

        Called once per conversation — when the first user message arrives.
        Title is truncated to 200 chars to match the DB column constraint.
        """
        conversation.title = title[:200]
        await db.flush()
        return conversation

    async def touch(
        self,
        db: AsyncSession,
        conversation: Conversation,
    ) -> Conversation:
        """
        Update last_message_at to now.

        Called every time a new message is saved to this conversation.
        Keeps the sidebar "most recent" sort accurate.
        """
        conversation.last_message_at = datetime.now(timezone.utc)
        await db.flush()
        return conversation


conversation_repo = ConversationRepository()
