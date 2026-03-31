"""
Chat router -- AI conversation endpoints.

Two endpoints:
1. POST /chat -- send a message, get an AI response
2. GET /history/{space_id} -- get chat history for a room
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.services.claude_service import ClaudeService
from shared.auth.dependencies import get_current_user

router = APIRouter()


# ─── Request/Response Models ───

class ChatRequest(BaseModel):
    """POST /api/v1/ai/chat body"""
    space_id: str = Field(..., alias="spaceId")
    message: str = Field(..., min_length=1, max_length=2000)

    model_config = {"populate_by_name": True}


class ChatResponse(BaseModel):
    response: str
    space_id: str


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    created_at: str | None = None


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessage]
    space_id: str


# ─── Endpoints ───

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: dict = Depends(get_current_user),
):
    """
    Send a message to the AI room assistant.

    The AI has context about the room (name, elements, dimensions)
    and can answer questions about the space.

    WHY auth required?
    We need the user_id to store who sent the message.
    Also prevents anonymous spam of the Claude API (which costs money per request).
    """
    service = ClaudeService()
    try:
        response = await service.chat(
            space_id=request.space_id,
            user_id=user["id"],
            message=request.message,
        )
        return ChatResponse(response=response, space_id=request.space_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}",
        )


@router.get("/history/{space_id}", response_model=ChatHistoryResponse)
async def get_history(
    space_id: str,
    user: dict = Depends(get_current_user),
):
    """
    Get chat history for a room.

    WHY no pagination?
    For a learning project, returning the last 50 messages is fine.
    In production, you'd add ?page=1&limit=20 query parameters.
    """
    service = ClaudeService()
    messages = await service.get_history(space_id=space_id)
    return ChatHistoryResponse(
        messages=[
            ChatMessage(
                role=msg["role"],
                content=msg["content"],
                created_at=msg.get("created_at"),
            )
            for msg in messages
        ],
        space_id=space_id,
    )
