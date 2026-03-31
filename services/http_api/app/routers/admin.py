"""
Admin router -- manage elements, avatars, and maps.

These endpoints are admin-only. Regular users get 403.
The get_admin_user dependency handles the role check automatically.

WHY separate admin router?
1. All routes share the same auth requirement (admin role)
2. In production, you might add extra logging or rate limiting for admin actions
3. Clear separation of "user actions" vs "admin actions" in the code
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.admin_service import AdminService
from shared.auth.dependencies import get_admin_user
from shared.models.element import (
    AvatarResponse,
    CreateAvatarRequest,
    CreateElementRequest,
    CreateMapRequest,
    ElementResponse,
    MapResponse,
    UpdateElementRequest,
)

router = APIRouter()


@router.post("/admin/element", response_model=ElementResponse)
async def create_element(
    request: CreateElementRequest,
    user: dict = Depends(get_admin_user),
):
    """
    Create a new element type (tree, building, etc.).

    Elements are reusable assets. Once created, they can be placed in any space
    multiple times at different positions. Think of an element as a "stamp" and
    a space_element as a "stamp mark" on the canvas.

    Test spec expects:
    - 200 with {id} on success
    - 403 if user is not admin
    """
    service = AdminService()
    element_id = await service.create_element(
        image_url=request.imageUrl,
        width=request.width,
        height=request.height,
        static=request.static,
    )
    return ElementResponse(id=element_id)


@router.put("/admin/element/{element_id}")
async def update_element(
    element_id: str,
    request: UpdateElementRequest,
    user: dict = Depends(get_admin_user),
):
    """
    Update an element's image URL.

    Test spec expects:
    - 200 on success
    - 403 if user is not admin
    """
    service = AdminService()
    try:
        await service.update_element(element_id=element_id, image_url=request.imageUrl)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/admin/avatar", response_model=AvatarResponse)
async def create_avatar(
    request: CreateAvatarRequest,
    user: dict = Depends(get_admin_user),
):
    """
    Create a new avatar that users can select.

    Test spec expects:
    - 200 with {avatarId} on success
    - 403 if user is not admin
    """
    service = AdminService()
    avatar_id = await service.create_avatar(
        image_url=request.imageUrl,
        name=request.name,
    )
    return AvatarResponse(avatarId=avatar_id)


@router.post("/admin/map", response_model=MapResponse)
async def create_map(
    request: CreateMapRequest,
    user: dict = Depends(get_admin_user),
):
    """
    Create a map template.

    A map is a blueprint for spaces. It defines:
    - Dimensions (width x height)
    - Default elements (pre-placed items at specific positions)
    - Thumbnail (preview image)

    When a user creates a space with this mapId, the space inherits
    the dimensions and gets copies of all default elements.

    Test spec expects:
    - 200 with {id} on success
    - 403 if user is not admin
    """
    service = AdminService()
    try:
        map_id = await service.create_map(
            thumbnail=request.thumbnail,
            dimensions=request.dimensions,
            name=request.name,
            default_elements=request.defaultElements,
        )
        return MapResponse(id=map_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
