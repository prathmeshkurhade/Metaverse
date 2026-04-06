"""
Space router -- CRUD operations for 2D metaverse rooms.

A "space" is a room in the metaverse with:
- Dimensions (width x height in grid units)
- Elements placed at specific positions (trees, buildings, etc.)
- Users who can join via WebSocket to move around

Spaces can be created from a map template (which pre-populates elements)
or as empty rooms with just dimensions.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.space_service import SpaceService
from shared.auth.dependencies import get_current_user
from shared.models.space import (
    AddElementRequest,
    CreateSpaceRequest,
    CreateSpaceResponse,
    DeleteElementRequest,
    SpaceDetailResponse,
    SpaceListResponse,
)

router = APIRouter()


@router.post("/space", response_model=CreateSpaceResponse)
async def create_space(
    request: CreateSpaceRequest,
    user: dict = Depends(get_current_user),
):
    """
    Create a new space (room).

    Two modes:
    1. With mapId: space inherits the map's dimensions and default elements
    2. Without mapId: must provide dimensions, space starts empty

    Test spec expects:
    - 200 with {spaceId} on success
    - 400 if neither mapId nor dimensions provided
    """
    service = SpaceService()
    try:
        space_id = await service.create_space(
            name=request.name,
            dimensions=request.dimensions,
            map_id=request.mapId,
            creator_id=user["id"],
            is_public=request.isPublic,
        )
        return CreateSpaceResponse(spaceId=space_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/space/{space_id}")
async def delete_space(
    space_id: str,
    user: dict = Depends(get_current_user),
):
    """
    Delete a space. Only the creator can delete their own spaces.

    Test spec expects:
    - 200 on success
    - 400 if space doesn't exist
    - 403 if user is not the creator
    """
    service = SpaceService()
    try:
        await service.delete_space(space_id=space_id, user_id=user["id"])
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own spaces",
        )


@router.get("/space/all", response_model=SpaceListResponse)
async def list_spaces(user: dict = Depends(get_current_user)):
    """List all spaces owned by the current user."""
    service = SpaceService()
    spaces = await service.list_spaces(user_id=user["id"])
    return SpaceListResponse(spaces=spaces)


@router.get("/space/public", response_model=SpaceListResponse)
async def list_public_spaces(user: dict = Depends(get_current_user)):
    """List all public spaces from all users. Anyone can join these."""
    service = SpaceService()
    spaces = await service.list_public_spaces()
    return SpaceListResponse(spaces=spaces)


@router.get("/space/{space_id}", response_model=SpaceDetailResponse)
async def get_space(
    space_id: str,
    user: dict = Depends(get_current_user),
):
    """
    Get a space's details including all placed elements.

    Test spec expects:
    - 200 with {dimensions, elements: [{id, elementId, x, y}]}
    - 400 if space doesn't exist
    """
    service = SpaceService()
    try:
        return await service.get_space(space_id=space_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/space/element")
async def add_element_to_space(
    request: AddElementRequest,
    user: dict = Depends(get_current_user),
):
    """
    Place an element at a specific position in a space.

    Test spec expects:
    - 200 on success
    - 400 if position is outside space dimensions
    """
    service = SpaceService()
    try:
        await service.add_element(
            space_id=request.spaceId,
            element_id=request.elementId,
            x=request.x,
            y=request.y,
        )
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/space/element")
async def delete_element_from_space(
    request: DeleteElementRequest,
    user: dict = Depends(get_current_user),
):
    """
    Remove an element instance from a space.

    Note: this deletes the space_element (the placement), not the element type itself.
    The element type still exists and can be placed again.
    """
    service = SpaceService()
    try:
        await service.delete_element(space_element_id=request.id)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
