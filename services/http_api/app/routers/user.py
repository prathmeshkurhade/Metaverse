"""
User router -- metadata and avatar endpoints.

These endpoints let users:
1. Set their avatar (which character they appear as in the 2D world)
2. Get other users' avatar info (so you can render their avatars in your view)
3. List all available avatars

WHY user metadata is separate from auth?
Auth handles identity (who you are). Metadata handles appearance (what you look like).
Different concerns, different router. Also, metadata endpoints have different
auth requirements (some are public, some require login).
"""

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.services.user_service import UserService
from shared.auth.dependencies import get_current_user
from shared.models.user import (
    AvatarListResponse,
    BulkMetadataResponse,
    UpdateMetadataRequest,
)

router = APIRouter()


@router.post("/user/metadata")
async def update_metadata(
    request: UpdateMetadataRequest,
    user: dict = Depends(get_current_user),
):
    """
    Set the current user's avatar.

    Test spec expects:
    - 200 on success
    - 400 if avatarId doesn't exist
    - 403 if no auth token
    """
    service = UserService()
    try:
        await service.update_metadata(user_id=user["id"], avatar_id=request.avatarId)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/user/metadata/bulk", response_model=BulkMetadataResponse)
async def get_bulk_metadata(ids: str = Query(...)):
    """
    Get avatar info for multiple users at once.

    WHY bulk instead of individual?
    When you join a space with 20 users, you need all their avatars.
    Making 20 separate API calls is slow. One bulk call is fast.

    The test spec sends ids as a JSON array in the query string:
    GET /api/v1/user/metadata/bulk?ids=[userId1,userId2]

    WHY is this public (no auth)?
    You need to see other users' avatars even before fully loading.
    Avatar info is not sensitive data.
    """
    service = UserService()
    # Parse the ids from the query string -- test sends "[id1,id2]" format
    try:
        parsed_ids = json.loads(ids)
        if not isinstance(parsed_ids, list):
            parsed_ids = [parsed_ids]
        # Convert to strings in case they come as other types
        parsed_ids = [str(i) for i in parsed_ids]
    except (json.JSONDecodeError, TypeError):
        parsed_ids = [ids]

    avatars = await service.get_bulk_metadata(user_ids=parsed_ids)
    return BulkMetadataResponse(avatars=avatars)


@router.get("/avatars", response_model=AvatarListResponse)
async def list_avatars():
    """
    List all available avatars.

    WHY public?
    Users need to see available avatars before choosing one.
    This is read-only, non-sensitive data.
    """
    service = UserService()
    avatars = await service.list_avatars()
    return AvatarListResponse(avatars=avatars)
