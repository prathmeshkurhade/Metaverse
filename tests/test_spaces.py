"""
Space and Admin endpoint tests -- ported from JS test spec.

Tests space CRUD, element placement, and admin operations.
"""

from tests.conftest import auth_headers


class TestSpaceInfo:
    """Test: describe("Space information")"""

    def _create_map_with_elements(self, http_client, token):
        """Helper: create 2 elements and a map with 3 default placements."""
        # Create elements
        el1 = http_client.post("/api/v1/admin/element", json={
            "imageUrl": "https://example.com/tree.png",
            "width": 1, "height": 1, "static": True,
        }, headers=auth_headers(token))
        el2 = http_client.post("/api/v1/admin/element", json={
            "imageUrl": "https://example.com/building.png",
            "width": 1, "height": 1, "static": True,
        }, headers=auth_headers(token))
        el1_id = el1.json()["id"]
        el2_id = el2.json()["id"]

        # Create map with 3 default elements
        map_resp = http_client.post("/api/v1/admin/map", json={
            "thumbnail": "https://example.com/thumb.png",
            "dimensions": "100x200",
            "name": "Test Map",
            "defaultElements": [
                {"elementId": el1_id, "x": 20, "y": 20},
                {"elementId": el1_id, "x": 18, "y": 20},
                {"elementId": el2_id, "x": 19, "y": 20},
            ],
        }, headers=auth_headers(token))
        return map_resp.json()["id"], el1_id, el2_id

    def test_user_can_create_space_with_map(self, http_client, admin_auth, user_auth):
        """JS: 'User is able to create a space'"""
        admin_token, _ = admin_auth
        user_token, _ = user_auth
        map_id, _, _ = self._create_map_with_elements(http_client, admin_token)

        resp = http_client.post("/api/v1/space", json={
            "name": "Test Space",
            "dimensions": "100x200",
            "mapId": map_id,
        }, headers=auth_headers(user_token))
        assert resp.status_code == 200
        assert "spaceId" in resp.json()

    def test_user_can_create_space_without_map(self, http_client, user_auth):
        """JS: 'User is able to create a space without mapId (empty space)'"""
        user_token, _ = user_auth

        resp = http_client.post("/api/v1/space", json={
            "name": "Empty Space",
            "dimensions": "100x200",
        }, headers=auth_headers(user_token))
        assert resp.status_code == 200
        assert "spaceId" in resp.json()

    def test_cannot_create_space_without_dimensions_or_map(self, http_client, user_auth):
        """JS: 'User is not able to create a space without mapId and dimensions'"""
        user_token, _ = user_auth

        resp = http_client.post("/api/v1/space", json={
            "name": "Bad Space",
        }, headers=auth_headers(user_token))
        assert resp.status_code == 400

    def test_cannot_delete_nonexistent_space(self, http_client, user_auth):
        """JS: 'User is not able to delete a space that doesnt exist'"""
        user_token, _ = user_auth

        resp = http_client.delete(
            "/api/v1/space/nonexistent-id",
            headers=auth_headers(user_token),
        )
        assert resp.status_code == 400

    def test_can_delete_own_space(self, http_client, user_auth):
        """JS: 'User is able to delete a space that does exist'"""
        user_token, _ = user_auth

        # Create
        create_resp = http_client.post("/api/v1/space", json={
            "name": "To Delete",
            "dimensions": "100x200",
        }, headers=auth_headers(user_token))
        space_id = create_resp.json()["spaceId"]

        # Delete
        del_resp = http_client.delete(
            f"/api/v1/space/{space_id}",
            headers=auth_headers(user_token),
        )
        assert del_resp.status_code == 200

    def test_cannot_delete_other_users_space(self, http_client, user_auth, admin_auth):
        """JS: 'User should not be able to delete a space created by another user'"""
        user_token, _ = user_auth
        admin_token, _ = admin_auth

        # User creates space
        create_resp = http_client.post("/api/v1/space", json={
            "name": "User's Space",
            "dimensions": "100x200",
        }, headers=auth_headers(user_token))
        space_id = create_resp.json()["spaceId"]

        # Admin tries to delete it
        del_resp = http_client.delete(
            f"/api/v1/space/{space_id}",
            headers=auth_headers(admin_token),
        )
        assert del_resp.status_code == 403

    def test_admin_has_no_spaces_initially(self, http_client, admin_auth):
        """JS: 'Admin has no spaces initially'"""
        admin_token, _ = admin_auth

        resp = http_client.get("/api/v1/space/all", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        assert len(resp.json()["spaces"]) == 0

    def test_admin_has_one_space_after_creation(self, http_client, admin_auth):
        """JS: 'Admin has gets once space after'"""
        admin_token, _ = admin_auth

        # Create
        http_client.post("/api/v1/space", json={
            "name": "Admin Space",
            "dimensions": "100x200",
        }, headers=auth_headers(admin_token))

        # List
        resp = http_client.get("/api/v1/space/all", headers=auth_headers(admin_token))
        assert len(resp.json()["spaces"]) == 1


class TestArenaEndpoints:
    """Test: describe("Arena endpoints")"""

    def test_incorrect_space_id_returns_400(self, http_client, user_auth):
        """JS: 'Incorrect spaceId returns a 400'"""
        user_token, _ = user_auth

        resp = http_client.get(
            "/api/v1/space/nonexistent123",
            headers=auth_headers(user_token),
        )
        assert resp.status_code == 400

    def test_correct_space_returns_elements(self, http_client, admin_auth, user_auth):
        """JS: 'Correct spaceId returns all the elements'"""
        admin_token, _ = admin_auth
        user_token, _ = user_auth

        # Setup: create elements, map, space
        el_resp = http_client.post("/api/v1/admin/element", json={
            "imageUrl": "https://example.com/el.png",
            "width": 1, "height": 1, "static": True,
        }, headers=auth_headers(admin_token))
        el_id = el_resp.json()["id"]

        map_resp = http_client.post("/api/v1/admin/map", json={
            "thumbnail": "https://example.com/thumb.png",
            "dimensions": "100x200",
            "name": "Arena Map",
            "defaultElements": [
                {"elementId": el_id, "x": 20, "y": 20},
                {"elementId": el_id, "x": 18, "y": 20},
                {"elementId": el_id, "x": 19, "y": 20},
            ],
        }, headers=auth_headers(admin_token))
        map_id = map_resp.json()["id"]

        space_resp = http_client.post("/api/v1/space", json={
            "name": "Arena", "dimensions": "100x200", "mapId": map_id,
        }, headers=auth_headers(user_token))
        space_id = space_resp.json()["spaceId"]

        # Get space details
        resp = http_client.get(
            f"/api/v1/space/{space_id}",
            headers=auth_headers(user_token),
        )
        assert resp.status_code == 200
        assert resp.json()["dimensions"] == "100x200"
        assert len(resp.json()["elements"]) == 3

    def test_adding_element_outside_dimensions_fails(self, http_client, admin_auth, user_auth):
        """JS: 'Adding an element fails if the element lies outside the dimensions'"""
        admin_token, _ = admin_auth
        user_token, _ = user_auth

        el_resp = http_client.post("/api/v1/admin/element", json={
            "imageUrl": "https://example.com/el.png",
            "width": 1, "height": 1, "static": True,
        }, headers=auth_headers(admin_token))
        el_id = el_resp.json()["id"]

        space_resp = http_client.post("/api/v1/space", json={
            "name": "Small Room", "dimensions": "100x200",
        }, headers=auth_headers(user_token))
        space_id = space_resp.json()["spaceId"]

        resp = http_client.post("/api/v1/space/element", json={
            "elementId": el_id,
            "spaceId": space_id,
            "x": 10000,
            "y": 210000,
        }, headers=auth_headers(user_token))
        assert resp.status_code == 400


class TestAdminEndpoints:
    """Test: describe("Admin Endpoints")"""

    def test_user_cannot_hit_admin_endpoints(self, http_client, user_auth):
        """JS: 'User is not able to hit admin Endpoints'"""
        user_token, _ = user_auth

        el_resp = http_client.post("/api/v1/admin/element", json={
            "imageUrl": "https://example.com/el.png",
            "width": 1, "height": 1, "static": True,
        }, headers=auth_headers(user_token))

        map_resp = http_client.post("/api/v1/admin/map", json={
            "thumbnail": "https://example.com/thumb.png",
            "dimensions": "100x200",
            "name": "test",
            "defaultElements": [],
        }, headers=auth_headers(user_token))

        avatar_resp = http_client.post("/api/v1/admin/avatar", json={
            "imageUrl": "https://example.com/avatar.png",
            "name": "Timmy",
        }, headers=auth_headers(user_token))

        assert el_resp.status_code == 403
        assert map_resp.status_code == 403
        assert avatar_resp.status_code == 403

    def test_admin_can_hit_admin_endpoints(self, http_client, admin_auth):
        """JS: 'Admin is able to hit admin Endpoints'"""
        admin_token, _ = admin_auth

        el_resp = http_client.post("/api/v1/admin/element", json={
            "imageUrl": "https://example.com/el.png",
            "width": 1, "height": 1, "static": True,
        }, headers=auth_headers(admin_token))

        map_resp = http_client.post("/api/v1/admin/map", json={
            "thumbnail": "https://example.com/thumb.png",
            "dimensions": "100x200",
            "name": "Admin Map",
            "defaultElements": [],
        }, headers=auth_headers(admin_token))

        avatar_resp = http_client.post("/api/v1/admin/avatar", json={
            "imageUrl": "https://example.com/avatar.png",
            "name": "Timmy",
        }, headers=auth_headers(admin_token))

        assert el_resp.status_code == 200
        assert map_resp.status_code == 200
        assert avatar_resp.status_code == 200

    def test_admin_can_update_element(self, http_client, admin_auth):
        """JS: 'Admin is able to update the imageUrl for an element'"""
        admin_token, _ = admin_auth

        # Create
        el_resp = http_client.post("/api/v1/admin/element", json={
            "imageUrl": "https://example.com/old.png",
            "width": 1, "height": 1, "static": True,
        }, headers=auth_headers(admin_token))
        el_id = el_resp.json()["id"]

        # Update
        update_resp = http_client.put(f"/api/v1/admin/element/{el_id}", json={
            "imageUrl": "https://example.com/new.png",
        }, headers=auth_headers(admin_token))
        assert update_resp.status_code == 200
