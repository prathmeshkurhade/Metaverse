"""
Pydantic models for User-related requests and responses.

WHY separate Create/Response models?
- Create models validate INCOMING data (what the client sends)
- Response models control OUTGOING data (what we send back)

For example, SignupRequest has a password field, but UserResponse does NOT.
If we used the same model for both, we'd accidentally return the password hash
in API responses. This separation is a security best practice.

WHY Pydantic v2?
Pydantic v2 (which you use in Infinity) is 5-50x faster than v1 because it's
built on Rust. The API is slightly different (model_config instead of class Config,
ConfigDict instead of dict), but the concepts are the same.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """
    WHY str + Enum?
    Inheriting from str makes the enum JSON-serializable automatically.
    Without str, FastAPI would need custom serialization logic.
    The test spec uses "admin" and "user" as role values.
    """
    ADMIN = "admin"
    USER = "user"


# ─── Request Models ───

class SignupRequest(BaseModel):
    """POST /api/v1/signup body"""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)
    type: UserRole  # "admin" or "user" -- the test spec uses "type" not "role"


class SigninRequest(BaseModel):
    """POST /api/v1/signin body"""
    username: str
    password: str


class UpdateMetadataRequest(BaseModel):
    """POST /api/v1/user/metadata body -- set the user's avatar"""
    avatarId: str  # camelCase because the test spec sends camelCase


# ─── Response Models ───

class SignupResponse(BaseModel):
    userId: str


class SigninResponse(BaseModel):
    token: str


class AvatarInfo(BaseModel):
    """Used in bulk metadata responses"""
    userId: str
    avatarId: Optional[str] = None


class BulkMetadataResponse(BaseModel):
    avatars: list[AvatarInfo]


class AvatarItem(BaseModel):
    id: str
    imageUrl: Optional[str] = None
    name: Optional[str] = None


class AvatarListResponse(BaseModel):
    avatars: list[AvatarItem]
