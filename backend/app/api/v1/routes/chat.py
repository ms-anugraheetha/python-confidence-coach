"""
app/api/v1/routes/chat.py — The main chat endpoint.

ROUTES:
  POST /api/v1/chat/message — send a message, get the AI response

This route is intentionally thin:
  1. Validate the request (Pydantic does this automatically)
  2. Verify the conversation belongs to this user
  3. Delegate all logic to chat_service.handle_message()
  4. Return the response

The coaching loop (explain → check → assess → re-explain) lives in
chat_service.py, not here.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.chat import MessageResponse, SendMessageRequest, SendMessageResponse
from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.security import get_current_user_id
from app.db.repositories.conversation_repo import conversation_repo
from app.db.session import get_db
from app.services.chat_service import handle_message

router = APIRouter()


@router.post("/chat/message", response_model=SendMessageResponse)
async def send_message(
    data: SendMessageRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SendMessageResponse:
    """
    Send a user message and get the AI coach response.

    The service automatically detects whether this is:
      - A new Python question (Path A: explain + check)
      - An answer to the confidence check (Path B: assess + affirm/re-explain)

    Both paths return a user_message + assistant_message pair.
    The assistant_message has confidence_check=True and check_question
    populated when the coach is asking a comprehension question.
    """
    # Verify the conversation exists and belongs to this user
    convo = await conversation_repo.get_by_id(db, data.conversation_id)
    if not convo:
        raise NotFoundError("Conversation", data.conversation_id)
    if convo.user_id != user_id:
        raise AuthorizationError("You don't have access to this conversation.")

    user_msg, assistant_msg = await handle_message(
        db=db,
        user_id=user_id,
        conversation_id=data.conversation_id,
        content=data.content,
    )

    return SendMessageResponse(
        user_message=MessageResponse.from_model(user_msg),
        assistant_message=MessageResponse.from_model(assistant_msg),
    )
