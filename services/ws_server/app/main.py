"""
WebSocket Server -- real-time communication for the 2D Metaverse.

This service handles:
- Users joining rooms (spaces)
- Real-time position updates as users move
- Broadcasting join/leave/move events to all users in a room

WHY a separate service from the HTTP API?
WebSocket connections are LONG-LIVED (minutes to hours). HTTP requests are
SHORT-LIVED (milliseconds). Mixing them in one process means:
1. A spike in HTTP requests could starve WebSocket connections of CPU
2. A WebSocket memory leak could crash the HTTP API
3. You can't scale them independently (you might need 5 WS servers but 1 HTTP)

This is THE core reason microservices exist -- different workloads need
different scaling strategies.

MESSAGE PROTOCOL (from test spec):

Client -> Server:
  {"type": "join", "payload": {"spaceId": "...", "token": "jwt..."}}
  {"type": "move", "payload": {"x": 5, "y": 10}}

Server -> Client:
  {"type": "space-joined", "payload": {"spawn": {"x": 3, "y": 7}, "users": [...]}}
  {"type": "user-joined", "payload": {"userId": "...", "x": 3, "y": 7}}
  {"type": "movement", "payload": {"userId": "...", "x": 5, "y": 10}}
  {"type": "movement-rejected", "payload": {"x": 3, "y": 7}}
  {"type": "user-left", "payload": {"userId": "..."}}
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.room_manager import RoomManager
from shared.auth.dependencies import get_current_user_from_token
from shared.database import supabase

app = FastAPI(title="Metaverse WebSocket Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single RoomManager instance for this process.
# WHY module-level? All WebSocket connections in this process share the same
# room state. If we created a new RoomManager per connection, users couldn't
# see each other.
room_manager = RoomManager()


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ws-server"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket handler.

    LIFECYCLE:
    1. Client connects (WebSocket handshake)
    2. Client sends "join" message with spaceId and JWT token
    3. Server validates token, adds user to room, sends "space-joined"
    4. Client sends "move" messages, server validates and broadcasts
    5. Client disconnects -> server broadcasts "user-left"

    WHY accept() before any validation?
    The WebSocket protocol requires accepting the connection before sending
    any data. We can't reject a WebSocket connection with an HTTP error
    (that's an HTTP concept). Instead, we accept, then close if invalid.
    """
    await websocket.accept()

    user_id = None

    try:
        while True:
            # Wait for a message from the client
            raw = await websocket.receive_text()
            data = json.loads(raw)

            msg_type = data.get("type")
            payload = data.get("payload", {})

            if msg_type == "join":
                user_id = await _handle_join(websocket, payload)

            elif msg_type == "move":
                if user_id:
                    await room_manager.handle_move(
                        user_id=user_id,
                        new_x=payload.get("x", 0),
                        new_y=payload.get("y", 0),
                    )

    except WebSocketDisconnect:
        # Client disconnected (closed tab, network issue, etc.)
        # WHY catch this specifically? FastAPI raises WebSocketDisconnect
        # when the client closes the connection. Without this catch,
        # the error would propagate and crash the handler.
        pass
    except json.JSONDecodeError:
        # Client sent invalid JSON -- close gracefully
        pass
    except Exception:
        # Catch-all for unexpected errors. In production, log this.
        pass
    finally:
        # ALWAYS clean up, no matter how the connection ended.
        # WHY in finally? Even if an exception occurs, we need to remove
        # the user from the room and notify others. Without this, "ghost"
        # users would appear in rooms forever.
        if user_id:
            await room_manager.leave_room(user_id)


async def _handle_join(websocket: WebSocket, payload: dict) -> str | None:
    """
    Process a "join" message.

    Steps:
    1. Extract and validate JWT token from the payload
    2. Fetch space dimensions from database
    3. Add user to the room via RoomManager
    4. Send "space-joined" response with spawn position and existing users

    Returns the user_id if successful, None if validation fails.
    """
    token = payload.get("token")
    space_id = payload.get("spaceId")

    if not token or not space_id:
        await websocket.send_text(json.dumps({
            "type": "error",
            "payload": {"message": "Missing token or spaceId"},
        }))
        return None

    # Validate the JWT token
    user = get_current_user_from_token(token)
    if not user:
        await websocket.send_text(json.dumps({
            "type": "error",
            "payload": {"message": "Invalid token"},
        }))
        return None

    user_id = user["id"]

    # Get space dimensions from database
    space = (
        supabase.table("spaces")
        .select("width, height")
        .eq("id", space_id)
        .execute()
    )
    if not space.data:
        await websocket.send_text(json.dumps({
            "type": "error",
            "payload": {"message": "Space not found"},
        }))
        return None

    width = space.data[0]["width"]
    height = space.data[0]["height"]

    # Fetch static elements to build collision map
    elements = (
        supabase.table("space_elements")
        .select("x, y")
        .eq("space_id", space_id)
        .execute()
    )
    blocked_tiles = {(el["x"], el["y"]) for el in elements.data}

    # Join the room
    spawn_x, spawn_y, existing_users = await room_manager.join_room(
        space_id=space_id,
        user_id=user_id,
        websocket=websocket,
        width=width,
        height=height,
        blocked_tiles=blocked_tiles,
    )

    # Send "space-joined" back to this user
    await websocket.send_text(json.dumps({
        "type": "space-joined",
        "payload": {
            "spawn": {"x": spawn_x, "y": spawn_y},
            "users": existing_users,
        },
    }))

    return user_id
