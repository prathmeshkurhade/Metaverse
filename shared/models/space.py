"""
Pydantic models for Space-related requests and responses.

A "space" is a 2D room in the metaverse. It has dimensions (width x height),
can be created from a map template (which pre-populates elements), and users
can join it via WebSocket to move around in real-time.
"""

from typing import Optional

from pydantic import BaseModel, Field


# ─── Request Models ───

class CreateSpaceRequest(BaseModel):
    """POST /api/v1/space body"""
    name: str = Field(..., min_length=1)
    # dimensions format: "100x200" (width x height)
    # WHY a string instead of separate width/height fields?
    # Because the test spec sends "dimensions": "100x200" as a single string.
    # We parse it in the service layer. Not ideal API design, but matches the spec.
    dimensions: Optional[str] = None
    mapId: Optional[str] = None  # If provided, space inherits map's dimensions and elements


class AddElementRequest(BaseModel):
    """POST /api/v1/space/element body -- add an element instance to a space"""
    elementId: str
    spaceId: str
    x: int
    y: int


class DeleteElementRequest(BaseModel):
    """DELETE /api/v1/space/element body -- remove an element instance from a space"""
    id: str  # The space_element ID (the instance, not the element type)


# ─── Response Models ───

class CreateSpaceResponse(BaseModel):
    spaceId: str


class SpaceElement(BaseModel):
    """An element placed in a space, with its position"""
    id: str
    elementId: str
    x: int
    y: int


class SpaceDetailResponse(BaseModel):
    """GET /api/v1/space/:id response"""
    dimensions: str  # "100x200"
    elements: list[SpaceElement]


class SpaceListItem(BaseModel):
    id: str
    name: str
    dimensions: str
    thumbnail: Optional[str] = None


class SpaceListResponse(BaseModel):
    spaces: list[SpaceListItem]
