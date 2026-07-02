"""app/api/v1/schemas/chat.py — Request/response schemas for chat routes."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.message import Message


class SendMessageRequest(BaseModel):
    conversation_id: uuid.UUID
    content: str = Field(min_length=1, max_length=8000)


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    topic_detected: str | None
    confidence_check: bool
    check_question: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, msg: Message) -> "MessageResponse":
        """
        Build a MessageResponse from a Message ORM object.

        Extracts confidence_check and check_question from tool_calls_json
        rather than storing them as separate columns.
        """
        check_question: str | None = None
        confidence_check = False

        if msg.tool_calls_json:
            raw = msg.tool_calls_json.get("check_question")
            if raw:
                check_question = str(raw)
                confidence_check = True

        return cls(
            id=msg.id,
            conversation_id=msg.conversation_id,
            role=msg.role,
            content=msg.content,
            topic_detected=msg.topic_detected,
            confidence_check=confidence_check,
            check_question=check_question,
            created_at=msg.created_at,
        )


class SendMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: str | None
    last_message_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
