"""
Authentication service -- business logic for signup and signin.

WHY a service class?
The router (auth.py) handles HTTP. This service handles logic.
Benefits:
1. Testable without HTTP -- just instantiate AuthService() and call methods
2. Reusable -- the WebSocket server also needs to verify tokens
3. Single responsibility -- if you change how passwords are hashed, only this file changes
"""

from shared.auth.dependencies import create_access_token, hash_password, verify_password
from shared.database import supabase


class AuthService:
    async def signup(self, username: str, password: str, role: str) -> str:
        """
        Create a new user account.

        Steps:
        1. Check if username already exists (Supabase query)
        2. Hash the password (bcrypt -- never store plain text!)
        3. Insert into users table
        4. Return the new user's ID

        WHY check for existing user first?
        Supabase would throw a unique constraint error, but the error message
        would be a raw PostgreSQL error. By checking first, we return a clean
        "Username already exists" message.
        """
        # Check if username already taken
        existing = (
            supabase.table("users")
            .select("id")
            .eq("username", username)
            .execute()
        )
        if existing.data:
            raise ValueError("Username already exists")

        # Hash password and insert
        hashed = hash_password(password)
        result = (
            supabase.table("users")
            .insert({
                "username": username,
                "password": hashed,
                "role": role,
            })
            .execute()
        )

        return result.data[0]["id"]

    async def signin(self, username: str, password: str) -> str:
        """
        Authenticate a user and return a JWT.

        Steps:
        1. Find user by username
        2. Verify password against stored bcrypt hash
        3. Create JWT with user_id and role baked in
        4. Return the token

        WHY return a token instead of a session?
        JWTs are stateless -- the server doesn't need to store session data.
        This is critical for microservices because any service can verify
        the token independently without calling a shared session store.
        In a session-based system, every request would need to hit a central
        Redis/database to validate the session. With JWTs, verification is
        just a cryptographic check using the shared secret.
        """
        # Find user
        result = (
            supabase.table("users")
            .select("id, password, role")
            .eq("username", username)
            .execute()
        )
        if not result.data:
            raise ValueError("User not found")

        user = result.data[0]

        # Verify password
        if not verify_password(password, user["password"]):
            raise ValueError("Invalid password")

        # Create and return JWT
        return create_access_token(user_id=user["id"], role=user["role"])
