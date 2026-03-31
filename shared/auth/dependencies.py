"""
JWT authentication dependencies for FastAPI.

WHY custom auth instead of Supabase Auth?
The test spec (index.test.js) expects username/password signup with type "admin"/"user".
Supabase Auth uses email-based signup and doesn't have custom roles built in.
So we manage our own users table and sign our own JWTs.

HOW JWTs WORK (the flow):
1. User signs up: we hash their password with bcrypt, store in DB
2. User signs in: we verify password, create a JWT containing {user_id, role}
3. User sends JWT in Authorization header: "Bearer <token>"
4. On every protected request, we decode the JWT, extract user_id and role
5. If the token is expired or tampered with, we reject the request

WHY bcrypt for passwords?
bcrypt is specifically designed for password hashing. It's intentionally SLOW
(~100ms per hash) which makes brute-force attacks impractical. Regular hashing
(SHA256) is fast = bad for passwords because attackers can try billions per second.

WHY HS256 for JWTs?
HS256 (HMAC-SHA256) is symmetric -- the same secret signs and verifies.
This is fine when only our own servers verify tokens. If third parties needed
to verify (without knowing the secret), we'd use RS256 or ES256 (asymmetric).
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from shared.config import settings

# HTTPBearer extracts the token from "Authorization: Bearer <token>" header.
# WHY HTTPBearer instead of manually parsing headers?
# FastAPI auto-generates the "Authorize" button in Swagger docs,
# and returns 403 automatically if the header is missing.
_bearer_scheme = HTTPBearer()


# ─── Password Hashing ───

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    bcrypt.gensalt() generates a random salt (random bytes mixed into the hash).
    WHY salt? Without it, two users with password "123456" would have identical hashes.
    With salt, each hash is unique even for the same password. The salt is stored
    inside the hash string itself, so you don't need to store it separately.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain password matches its bcrypt hash.

    bcrypt.checkpw extracts the salt from the stored hash, re-hashes the
    plain password with that salt, and compares. This is why you don't need
    to store the salt separately.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ─── JWT Creation ───

def create_access_token(user_id: str, role: str) -> str:
    """
    Create a signed JWT containing the user's ID and role.

    The token payload contains:
    - sub (subject): the user's ID -- standard JWT claim for "who this token is about"
    - role: "admin" or "user" -- our custom claim for authorization
    - exp (expiration): when this token stops being valid
    - iat (issued at): when this token was created (useful for debugging)

    WHY include role in the token?
    So we don't need a database query on every request to check if a user is admin.
    The role is "baked into" the token at sign-in time. If a user's role changes,
    they need to re-login to get a new token. This trade-off (stale role for up to
    1 hour) is acceptable for our use case.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES),
        "iat": now,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


# ─── JWT Verification (FastAPI Dependencies) ───

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """
    FastAPI dependency that extracts and validates the JWT from the request.

    Used like this in a router:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            print(user["id"], user["role"])

    WHY return a dict instead of a Pydantic model?
    Simplicity. The auth dependency is called on every protected request.
    A dict avoids the overhead of model validation for something this simple.
    The Infinity project uses the same pattern.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token: missing user ID",
            )
        return {"id": user_id, "role": role}
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid or expired token: {exc}",
        )


def get_current_user_from_token(token: str) -> dict | None:
    """
    Validate a JWT token string directly (no FastAPI dependency injection).

    WHY this exists?
    WebSocket connections don't have HTTP headers in the same way as REST requests.
    The token is sent inside the WebSocket message payload ({"type": "join", "payload": {"token": "..."}}).
    FastAPI's Depends(get_current_user) only works with HTTP requests.
    So the WebSocket server calls this function directly with the token string.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None:
            return None
        return {"id": user_id, "role": role}
    except JWTError:
        return None


def get_current_user_id(user: dict = Depends(get_current_user)) -> str:
    """Convenience dependency that returns just the user ID string."""
    return user["id"]


def get_admin_user(user: dict = Depends(get_current_user)) -> dict:
    """
    FastAPI dependency that requires the user to be an admin.

    Used on admin-only routes:
        @router.post("/admin/element")
        async def create_element(user: dict = Depends(get_admin_user)):
            ...

    WHY a separate dependency instead of checking role in every route?
    DRY (Don't Repeat Yourself). Without this, every admin route would need:
        if user["role"] != "admin": raise HTTPException(403)
    With this dependency, the check happens automatically before the route runs.
    """
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
