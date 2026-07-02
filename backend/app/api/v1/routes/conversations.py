"""
app/api/v1/routes/conversations.py — Conversation management endpoints.

ROUTES:
  POST /api/v1/conversations           — start a new conversation
  GET  /api/v1/conversations           — list user's conversations (sidebar)
  GET  /api/v1/conversations/{id}/messages — load full message history
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.chat import ConversationResponse, MessageResponse
from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.security import get_current_user_id
from app.db.repositories.conversation_repo import conversation_repo
from app.db.repositories.message_repo import message_repo
from app.db.session import get_db

router = APIRouter(prefix="/conversations")


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationResponse:
    """
    Start a new (empty) conversation.

    Called by the frontend when the user clicks "New chat" or sends
    their first message. Title is null until the first message is saved.
    """
    convo = await conversation_repo.create(db, user_id=user_id)
    return ConversationResponse.model_validate(convo)


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ConversationResponse]:
    """
    List the user's conversations, newest first.
    Used to populate the conversation history sidebar.
    """
    convos = await conversation_repo.list_for_user(db, user_id, limit=30)
    return [ConversationResponse.model_validate(c) for c in convos]


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MessageResponse]:
    """
    Return all messages in a conversation, chronological order.
    Used when the user clicks a conversation in the sidebar to reload it.
    """
    convo = await conversation_repo.get_by_id(db, conversation_id)
    if not convo:
        raise NotFoundError("Conversation", conversation_id)
    if convo.user_id != user_id:
        raise AuthorizationError("You don't have access to this conversation.")

    msgs = await message_repo.list_for_conversation(db, conversation_id)
    return [MessageResponse.from_model(m) for m in msgs]
