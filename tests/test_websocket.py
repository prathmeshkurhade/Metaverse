"""
WebSocket tests -- ported from JS test spec (index.test.js lines 792-1039).

These tests verify the real-time WebSocket behavior:
- Joining a room and receiving spawn position
- Broadcasting join events to other users
- Movement validation (boundary checks, max 1 unit)
- Broadcasting movement to other users
- Leave/disconnect notifications

NOTE: These tests require BOTH the HTTP API (port 8000) and WebSocket server
(port 8001) to be running. They are integration tests, not unit tests.
"""

import json
import time

import httpx
import websocket as ws_lib  # websocket-client library (sync)

from tests.conftest import auth_headers

HTTP_BASE = "http://localhost:8000"
WS_URL = "ws://localhost:8001/ws"


def create_test_setup():
    """Create admin, user, elements, map, and space for WebSocket tests."""
    client = httpx.Client(base_url=HTTP_BASE, timeout=10.0)

    import random
    username = f"wstest-{random.randint(10000, 99999)}"
    password = "123456"

    # Create admin
    admin_signup = client.post("/api/v1/signup", json={
        "username": username, "password": password, "type": "admin",
    })
    admin_user_id = admin_signup.json()["userId"]
    admin_token = client.post("/api/v1/signin", json={
        "username": username, "password": password,
    }).json()["token"]

    # Create regular user
    user_signup = client.post("/api/v1/signup", json={
        "username": f"{username}-user", "password": password, "type": "user",
    })
    user_id = user_signup.json()["userId"]
    user_token = client.post("/api/v1/signin", json={
        "username": f"{username}-user", "password": password,
    }).json()["token"]

    # Create elements
    el1 = client.post("/api/v1/admin/element", json={
        "imageUrl": "https://example.com/el.png",
        "width": 1, "height": 1, "static": True,
    }, headers=auth_headers(admin_token)).json()["id"]

    # Create map
    map_id = client.post("/api/v1/admin/map", json={
        "thumbnail": "https://example.com/thumb.png",
        "dimensions": "100x200",
        "name": "WS Test Map",
        "defaultElements": [{"elementId": el1, "x": 20, "y": 20}],
    }, headers=auth_headers(admin_token)).json()["id"]

    # Create space
    space_id = client.post("/api/v1/space", json={
        "name": "WS Test Space", "dimensions": "100x200", "mapId": map_id,
    }, headers=auth_headers(user_token)).json()["spaceId"]

    client.close()

    return {
        "admin_token": admin_token,
        "admin_user_id": admin_user_id,
        "user_token": user_token,
        "user_id": user_id,
        "space_id": space_id,
    }


def wait_for_message(ws_conn, timeout=5):
    """Wait for a WebSocket message with timeout."""
    ws_conn.settimeout(timeout)
    try:
        raw = ws_conn.recv()
        return json.loads(raw)
    except Exception:
        return None


class TestWebSocket:
    """Test: describe("Websocket tests")"""

    def test_join_and_movement_flow(self):
        """
        Combined test covering:
        - 'Get back ack for joining the space'
        - 'User should not be able to move across the boundary of the wall'
        - 'User should not be able to move two blocks at the same time'
        - 'Correct movement should be broadcasted to the other sockets in the room'
        - 'If a user leaves, the other user receives a leave event'

        WHY one big test instead of separate?
        WebSocket tests are stateful -- each test depends on the state created
        by the previous one (user positions, room membership). Splitting them
        would require re-creating the entire setup for each test.
        """
        setup = create_test_setup()

        # Connect two WebSocket clients
        ws1 = ws_lib.create_connection(WS_URL)
        ws2 = ws_lib.create_connection(WS_URL)

        try:
            # ── Test: Join room ──
            # User 1 (admin) joins
            ws1.send(json.dumps({
                "type": "join",
                "payload": {
                    "spaceId": setup["space_id"],
                    "token": setup["admin_token"],
                },
            }))
            msg1 = wait_for_message(ws1)
            assert msg1["type"] == "space-joined"
            assert "spawn" in msg1["payload"]
            assert len(msg1["payload"]["users"]) == 0  # First user, no others

            admin_x = msg1["payload"]["spawn"]["x"]
            admin_y = msg1["payload"]["spawn"]["y"]

            # User 2 (regular user) joins
            ws2.send(json.dumps({
                "type": "join",
                "payload": {
                    "spaceId": setup["space_id"],
                    "token": setup["user_token"],
                },
            }))
            msg2 = wait_for_message(ws2)
            assert msg2["type"] == "space-joined"
            assert len(msg2["payload"]["users"]) == 1  # Sees admin

            user_x = msg2["payload"]["spawn"]["x"]
            user_y = msg2["payload"]["spawn"]["y"]

            # Admin should receive "user-joined" broadcast
            msg3 = wait_for_message(ws1)
            assert msg3["type"] == "user-joined"
            assert msg3["payload"]["userId"] == setup["user_id"]
            assert msg3["payload"]["x"] == user_x
            assert msg3["payload"]["y"] == user_y

            # ── Test: Movement rejected (out of bounds) ──
            ws1.send(json.dumps({
                "type": "move",
                "payload": {"x": 1000000, "y": 10000},
            }))
            msg4 = wait_for_message(ws1)
            assert msg4["type"] == "movement-rejected"
            assert msg4["payload"]["x"] == admin_x
            assert msg4["payload"]["y"] == admin_y

            # ── Test: Movement rejected (more than 1 block) ──
            ws1.send(json.dumps({
                "type": "move",
                "payload": {"x": admin_x + 2, "y": admin_y},
            }))
            msg5 = wait_for_message(ws1)
            assert msg5["type"] == "movement-rejected"
            assert msg5["payload"]["x"] == admin_x

            # ── Test: Valid movement broadcasts to others ──
            ws1.send(json.dumps({
                "type": "move",
                "payload": {"x": admin_x + 1, "y": admin_y},
            }))
            msg6 = wait_for_message(ws2)
            assert msg6["type"] == "movement"
            assert msg6["payload"]["x"] == admin_x + 1
            assert msg6["payload"]["y"] == admin_y

            # ── Test: Leave broadcasts to remaining users ──
            ws1.close()
            time.sleep(0.5)  # Brief wait for disconnect to propagate
            msg7 = wait_for_message(ws2)
            assert msg7["type"] == "user-left"
            assert msg7["payload"]["userId"] == setup["admin_user_id"]

        finally:
            try:
                ws1.close()
            except Exception:
                pass
            try:
                ws2.close()
            except Exception:
                pass
