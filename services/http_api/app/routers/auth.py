"""
Authentication router -- signup and signin endpoints.

FLOW:
  Signup: client sends {username, password, type} -> we hash password, store in DB, return userId
  Signin: client sends {username, password} -> we verify password, return JWT token

WHY separate router from service?
The router handles HTTP concerns (status codes, request parsing, response format).
The service handles business logic (password hashing, DB queries).
This separation means you can test business logic without spinning up an HTTP server,
and you can change HTTP behavior (e.g., add rate limiting) without touching logic.
"""

from fastapi import APIRouter, HTTPException, status

from app.services.auth_service import AuthService
from shared.models.user import SigninRequest, SigninResponse, SignupRequest, SignupResponse

router = APIRouter()


@router.post("/signup", response_model=SignupResponse)
async def signup(request: SignupRequest):
    """
    Register a new user.

    - Validates username is not taken
    - Hashes password with bcrypt
    - Stores user in Supabase
    - Returns the new user's ID

    Test spec expects:
    - 200 on success with {userId}
    - 400 if username already exists or username is missing
    """
    service = AuthService()
    try:
        user_id = await service.signup(
            username=request.username,
            password=request.password,
            role=request.type.value,  # .value converts enum to string "admin"/"user"
        )
        return SignupResponse(userId=user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/signin", response_model=SigninResponse)
async def signin(request: SigninRequest):
    """
    Authenticate a user and return a JWT.

    - Finds user by username
    - Verifies password against stored hash
    - Creates and returns a JWT

    Test spec expects:
    - 200 on success with {token}
    - 403 if username not found or password wrong
    """
    service = AuthService()
    try:
        token = await service.signin(
            username=request.username,
            password=request.password,
        )
        return SigninResponse(token=token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid username or password",
        )
