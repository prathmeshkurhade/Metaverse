"""
Room Manager -- the brain of the WebSocket server.

This class manages:
- Which users are in which rooms (spaces)
- Each user's position (x, y)
- WebSocket connections per user
- Broadcasting messages to everyone in a room

WHY a class instead of global variables?
Encapsulation. All room state is in one place. If you need to add features
(e.g., maximum users per room, user permissions), you modify this one class.
Global variables scattered across files would be a debugging nightmare.

WHY in-memory state (dicts) instead of database?
Real-time position data changes every time a user moves (potentially 10+ times/second).
Writing to a database on every move would be way too slow. In-memory dicts give
microsecond access times. The trade-off: if the server crashes, all position data
is lost. But that's fine -- users just rejoin and get new spawn positions.

SCALING NOTE:
This works for a single server. With multiple WebSocket servers, you'd need
Redis pub/sub to broadcast across instances. For learning purposes, single
server is perfect.
"""

import json
import random
from dataclasses import dataclass, field

from fastapi import WebSocket


@dataclass
class UserConnection:
    """
    Tracks a single user's state in a room.

    WHY a dataclass?
    Clean, typed container for related data. Better than a dict because
    typos (e.g., user["positon"]) are caught by the IDE, not at runtime.
    """
    user_id: str
    websocket: WebSocket
    x: int = 0
    y: int = 0


@dataclass
class Room:
    """
    A room (space) with its dimensions and connected users.

    users dict: maps user_id -> UserConnection
    WHY a dict instead of a list?
    O(1) lookup by user_id. When user A moves, we need to find user A's
    connection instantly. A list would require iterating through all users.
    """
    space_id: str
    width: int
    height: int
    users: dict[str, UserConnection] = field(default_factory=dict)


class RoomManager:
    """
    Manages all active rooms and their users.

    rooms dict: maps space_id -> Room
    user_rooms dict: maps user_id -> space_id (reverse lookup)

    WHY the reverse lookup?
    When a WebSocket disconnects, we know the user_id but not which room
    they were in. Without user_rooms, we'd have to search every room.
    """

    def __init__(self):
        self.rooms: dict[str, Room] = {}
        self.user_rooms: dict[str, str] = {}

    async def join_room(
        self, space_id: str, user_id: str, websocket: WebSocket,
        width: int, height: int,
    ) -> tuple[int, int, list[dict]]:
        """
        Add a user to a room.

        Returns:
        - (spawn_x, spawn_y): random spawn position for the new user
        - existing_users: list of {userId, x, y} for users already in the room

        SPAWN LOGIC:
        Random position within the room. In a real game, you'd have designated
        spawn points. For our purposes, random is fine. The test spec just checks
        that spawn coordinates exist, not their specific values.
        """
        # Create room if it doesn't exist
        if space_id not in self.rooms:
            self.rooms[space_id] = Room(
                space_id=space_id,
                width=width,
                height=height,
            )

        room = self.rooms[space_id]

        # Generate random spawn position
        # WHY max(1, ...) and min? Avoid spawning at the very edge (0) or outside bounds
        spawn_x = random.randint(0, max(0, width - 1))
        spawn_y = random.randint(0, max(0, height - 1))

        # Get list of existing users BEFORE adding the new one
        existing_users = [
            {"userId": uid, "x": conn.x, "y": conn.y}
            for uid, conn in room.users.items()
        ]

        # Add the new user
        room.users[user_id] = UserConnection(
            user_id=user_id,
            websocket=websocket,
            x=spawn_x,
            y=spawn_y,
        )
        self.user_rooms[user_id] = space_id

        # Broadcast "user-joined" to everyone ELSE in the room
        await self._broadcast_to_room(
            space_id,
            {
                "type": "user-joined",
                "payload": {
                    "userId": user_id,
                    "x": spawn_x,
                    "y": spawn_y,
                },
            },
            exclude_user=user_id,
        )

        return spawn_x, spawn_y, existing_users

    async def handle_move(
        self, user_id: str, new_x: int, new_y: int
    ) -> bool:
        """
        Process a movement request.

        VALIDATION RULES (from test spec):
        1. New position must be within room boundaries (0 <= x < width, 0 <= y < height)
        2. User can only move 1 unit at a time in any direction (Manhattan distance <= 1,
           or diagonal where both dx and dy are <= 1)

        WHY validate on the server?
        Never trust the client. A modified client could send x=99999 to teleport.
        Server-side validation is the only reliable way to enforce game rules.

        Returns True if move was valid, False if rejected.
        """
        space_id = self.user_rooms.get(user_id)
        if not space_id or space_id not in self.rooms:
            return False

        room = self.rooms[space_id]
        user_conn = room.users.get(user_id)
        if not user_conn:
            return False

        # Check 1: Within boundaries
        if new_x < 0 or new_x >= room.width or new_y < 0 or new_y >= room.height:
            await self._send_movement_rejected(user_conn)
            return False

        # Check 2: Maximum 1 unit movement in each axis
        dx = abs(new_x - user_conn.x)
        dy = abs(new_y - user_conn.y)
        if dx > 1 or dy > 1:
            await self._send_movement_rejected(user_conn)
            return False

        # Valid move -- update position
        user_conn.x = new_x
        user_conn.y = new_y

        # Broadcast movement to OTHER users in the room
        await self._broadcast_to_room(
            space_id,
            {
                "type": "movement",
                "payload": {
                    "userId": user_id,
                    "x": new_x,
                    "y": new_y,
                },
            },
            exclude_user=user_id,
        )

        return True

    async def leave_room(self, user_id: str) -> None:
        """
        Remove a user from their room (on disconnect or explicit leave).

        Broadcasts "user-left" to remaining users so their frontend
        can remove the avatar from the canvas.
        """
        space_id = self.user_rooms.pop(user_id, None)
        if not space_id or space_id not in self.rooms:
            return

        room = self.rooms[space_id]
        room.users.pop(user_id, None)

        # Broadcast departure
        await self._broadcast_to_room(
            space_id,
            {
                "type": "user-left",
                "payload": {"userId": user_id},
            },
        )

        # Clean up empty rooms to free memory
        if not room.users:
            del self.rooms[space_id]

    async def _send_movement_rejected(self, user_conn: UserConnection) -> None:
        """
        Tell a user their move was invalid, sending back their CURRENT position.

        WHY send current position?
        The client might have optimistically moved the avatar. Sending the
        server's authoritative position lets the client "snap back" to the
        correct location. This is the "server-authoritative" pattern used
        in all multiplayer games.
        """
        await user_conn.websocket.send_text(json.dumps({
            "type": "movement-rejected",
            "payload": {
                "x": user_conn.x,
                "y": user_conn.y,
            },
        }))

    async def _broadcast_to_room(
        self, space_id: str, message: dict, exclude_user: str | None = None
    ) -> None:
        """
        Send a message to all users in a room, optionally excluding one user.

        WHY exclude?
        When user A moves, we broadcast to everyone EXCEPT user A.
        User A already knows they moved (they sent the request).
        Sending it back would cause visual stuttering on their screen.

        WHY try/except per user?
        If one user's connection is broken, we don't want to fail the
        broadcast to everyone else. The broken connection will be cleaned
        up when the disconnect handler fires.
        """
        if space_id not in self.rooms:
            return

        room = self.rooms[space_id]
        message_text = json.dumps(message)

        for uid, conn in list(room.users.items()):
            if uid == exclude_user:
                continue
            try:
                await conn.websocket.send_text(message_text)
            except Exception:
                # Connection is broken -- will be cleaned up on disconnect
                pass
