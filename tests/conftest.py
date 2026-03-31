"""
Pytest configuration and shared fixtures.

WHY conftest.py?
Pytest automatically discovers conftest.py and makes its fixtures available
to ALL test files in the same directory (and subdirectories). Fixtures are
reusable setup/teardown helpers. Instead of repeating "create user, login,
get token" in every test, you define it once here as a fixture.

WHY httpx.AsyncClient instead of requests?
FastAPI's TestClient uses httpx under the hood. httpx supports async,
which matches our async FastAPI endpoints. Also, httpx.AsyncClient can
test the app directly (in-process, no network) OR against a running server.
"""

import sys
from pathlib import Path

# Add project root to path so shared package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
import httpx

# The base URLs -- change these if testing against running servers
HTTP_BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8001"


@pytest.fixture
def base_url():
    """Base URL for HTTP API tests."""
    return HTTP_BASE_URL


@pytest.fixture
def ws_url():
    """Base URL for WebSocket tests."""
    return WS_BASE_URL


@pytest.fixture
def http_client(base_url):
    """
    HTTP client for making API requests.

    WHY a fixture? So every test gets a fresh client. The client handles
    connection pooling, timeouts, and cleanup automatically.
    """
    return httpx.Client(base_url=base_url, timeout=10.0)


@pytest.fixture
def random_username():
    """Generate a unique username for test isolation."""
    import random
    return f"testuser-{random.randint(10000, 99999)}"


@pytest.fixture
def admin_auth(http_client, random_username):
    """
    Create an admin user and return (token, userId).

    WHY a fixture? Most tests need an authenticated admin.
    This fixture handles signup + signin in one step.
    """
    password = "testpass123"
    # Signup
    signup_resp = http_client.post("/api/v1/signup", json={
        "username": random_username,
        "password": password,
        "type": "admin",
    })
    assert signup_resp.status_code == 200
    user_id = signup_resp.json()["userId"]

    # Signin
    signin_resp = http_client.post("/api/v1/signin", json={
        "username": random_username,
        "password": password,
    })
    assert signin_resp.status_code == 200
    token = signin_resp.json()["token"]

    return token, user_id


@pytest.fixture
def user_auth(http_client):
    """Create a regular (non-admin) user and return (token, userId)."""
    import random
    username = f"testuser-{random.randint(10000, 99999)}"
    password = "testpass123"

    signup_resp = http_client.post("/api/v1/signup", json={
        "username": username,
        "password": password,
        "type": "user",
    })
    assert signup_resp.status_code == 200
    user_id = signup_resp.json()["userId"]

    signin_resp = http_client.post("/api/v1/signin", json={
        "username": username,
        "password": password,
    })
    assert signin_resp.status_code == 200
    token = signin_resp.json()["token"]

    return token, user_id


def auth_headers(token: str) -> dict:
    """Helper to create Authorization headers."""
    return {"Authorization": f"Bearer {token}"}
