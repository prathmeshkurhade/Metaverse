"""
Authentication tests -- ported from the JS test spec (index.test.js lines 41-108).

Each test mirrors a test from the original spec. Comments reference the
original test names so you can compare 1:1.
"""

from tests.conftest import auth_headers


class TestAuthentication:
    """Test: describe("Authentication")"""

    def test_user_can_signup_only_once(self, http_client, random_username):
        """JS: 'User is able to sign up only once'"""
        password = "123456"

        # First signup should succeed
        resp1 = http_client.post("/api/v1/signup", json={
            "username": random_username,
            "password": password,
            "type": "admin",
        })
        assert resp1.status_code == 200

        # Second signup with same username should fail
        resp2 = http_client.post("/api/v1/signup", json={
            "username": random_username,
            "password": password,
            "type": "admin",
        })
        assert resp2.status_code == 400

    def test_signup_fails_without_username(self, http_client):
        """JS: 'Signup request fails if the username is empty'"""
        resp = http_client.post("/api/v1/signup", json={
            "password": "123456",
        })
        # FastAPI returns 422 for validation errors (missing required field)
        assert resp.status_code == 422

    def test_signin_succeeds_with_correct_credentials(self, http_client, random_username):
        """JS: 'Signin succeeds if the username and password are correct'"""
        password = "123456"

        # Signup first
        http_client.post("/api/v1/signup", json={
            "username": random_username,
            "password": password,
            "type": "admin",
        })

        # Signin
        resp = http_client.post("/api/v1/signin", json={
            "username": random_username,
            "password": password,
        })
        assert resp.status_code == 200
        assert "token" in resp.json()

    def test_signin_fails_with_wrong_credentials(self, http_client, random_username):
        """JS: 'Signin fails if the username and password are incorrect'"""
        http_client.post("/api/v1/signup", json={
            "username": random_username,
            "password": "123456",
            "type": "admin",
        })

        resp = http_client.post("/api/v1/signin", json={
            "username": "WrongUsername",
            "password": "123456",
        })
        assert resp.status_code == 403


class TestUserMetadata:
    """Test: describe("User metadata endpoint")"""

    def test_cannot_update_metadata_with_wrong_avatar(self, http_client, admin_auth):
        """JS: 'User cant update their metadata with a wrong avatar id'"""
        token, _ = admin_auth

        resp = http_client.post("/api/v1/user/metadata", json={
            "avatarId": "999999",
        }, headers=auth_headers(token))
        assert resp.status_code == 400

    def test_can_update_metadata_with_valid_avatar(self, http_client, admin_auth):
        """JS: 'User can update their metadata with the right avatar id'"""
        token, _ = admin_auth

        # Create an avatar first (admin only)
        avatar_resp = http_client.post("/api/v1/admin/avatar", json={
            "imageUrl": "https://example.com/avatar.png",
            "name": "TestAvatar",
        }, headers=auth_headers(token))
        assert avatar_resp.status_code == 200
        avatar_id = avatar_resp.json()["avatarId"]

        # Update metadata
        resp = http_client.post("/api/v1/user/metadata", json={
            "avatarId": avatar_id,
        }, headers=auth_headers(token))
        assert resp.status_code == 200

    def test_cannot_update_metadata_without_auth(self, http_client):
        """JS: 'User is not able to update their metadata if the auth header is not present'"""
        resp = http_client.post("/api/v1/user/metadata", json={
            "avatarId": "1",
        })
        assert resp.status_code == 403


class TestUserAvatarInfo:
    """Test: describe("User avatar information")"""

    def test_get_avatar_info_for_user(self, http_client, admin_auth):
        """JS: 'Get back avatar information for a user'"""
        token, user_id = admin_auth

        resp = http_client.get(f'/api/v1/user/metadata/bulk?ids=["{user_id}"]')
        assert resp.status_code == 200
        assert len(resp.json()["avatars"]) == 1
        assert resp.json()["avatars"][0]["userId"] == user_id

    def test_available_avatars_lists_created_avatar(self, http_client, admin_auth):
        """JS: 'Available avatars lists the recently created avatar'"""
        token, _ = admin_auth

        # Create an avatar
        avatar_resp = http_client.post("/api/v1/admin/avatar", json={
            "imageUrl": "https://example.com/avatar2.png",
            "name": "TestAvatar2",
        }, headers=auth_headers(token))
        avatar_id = avatar_resp.json()["avatarId"]

        # List avatars
        resp = http_client.get("/api/v1/avatars")
        assert resp.status_code == 200
        avatars = resp.json()["avatars"]
        assert len(avatars) > 0
        assert any(a["id"] == avatar_id for a in avatars)
