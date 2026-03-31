"""
Pydantic models for Element, Avatar, and Map admin operations.

Elements = assets (trees, buildings, etc.) that can be placed in spaces.
Avatars = user representations shown in the 2D world.
Maps = templates for spaces (predefined layout of elements).

All create/update operations for these are admin-only endpoints.
"""

from typing import Optional

from pydantic import BaseModel, Field


# ─── Element Models ───

class CreateElementRequest(BaseModel):
    """POST /api/v1/admin/element body"""
    imageUrl: str
    width: int = Field(..., ge=1)
    height: int = Field(..., ge=1)
    static: bool = True  # WHY default True? Static elements can't be moved by users.


class UpdateElementRequest(BaseModel):
    """PUT /api/v1/admin/element/:id body"""
    imageUrl: str


class ElementResponse(BaseModel):
    id: str
    imageUrl: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    static: Optional[bool] = None


# ─── Avatar Models ───

class CreateAvatarRequest(BaseModel):
    """POST /api/v1/admin/avatar body"""
    imageUrl: str
    name: str = Field(..., min_length=1)


class AvatarResponse(BaseModel):
    avatarId: str


# ─── Map Models ───

class MapDefaultElement(BaseModel):
    """An element positioned on a map template"""
    elementId: str
    x: int
    y: int


class CreateMapRequest(BaseModel):
    """POST /api/v1/admin/map body"""
    thumbnail: str
    dimensions: str  # "100x200"
    name: str = Field(..., min_length=1)
    defaultElements: list[MapDefaultElement] = []


class MapResponse(BaseModel):
    id: str
