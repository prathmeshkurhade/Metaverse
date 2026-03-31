"""
User service -- business logic for metadata and avatar operations.
"""

from shared.database import supabase
from shared.models.user import AvatarInfo, AvatarItem


class UserService:
    async def update_metadata(self, user_id: str, avatar_id: str) -> None:
        """
        Set or update a user's selected avatar.

        Steps:
        1. Verify the avatar exists (don't let users pick non-existent avatars)
        2. Upsert into user_metadata table

        WHY upsert instead of insert?
        The first time a user picks an avatar, it's an insert.
        Every time after, it's an update. Upsert handles both cases.
        Supabase supports upsert via .upsert() with on_conflict.
        """
        # Verify avatar exists
        avatar = (
            supabase.table("avatars")
            .select("id")
            .eq("id", avatar_id)
            .execute()
        )
        if not avatar.data:
            raise ValueError("Avatar not found")

        # Upsert metadata -- if user_id row exists, update it; otherwise insert
        supabase.table("user_metadata").upsert(
            {"user_id": user_id, "avatar_id": avatar_id},
            on_conflict="user_id",
        ).execute()

    async def get_bulk_metadata(self, user_ids: list[str]) -> list[AvatarInfo]:
        """
        Get avatar selections for multiple users.

        Returns a list of {userId, avatarId} for each user that has selected an avatar.
        Users who haven't selected an avatar still appear (with avatarId=None).
        """
        if not user_ids:
            return []

        result = (
            supabase.table("user_metadata")
            .select("user_id, avatar_id")
            .in_("user_id", user_ids)
            .execute()
        )

        # Build a map of user_id -> avatar_id from results
        metadata_map = {row["user_id"]: row["avatar_id"] for row in result.data}

        # Return info for ALL requested users (even if they have no metadata)
        return [
            AvatarInfo(userId=uid, avatarId=metadata_map.get(uid))
            for uid in user_ids
        ]

    async def list_avatars(self) -> list[AvatarItem]:
        """List all available avatars."""
        result = supabase.table("avatars").select("id, image_url, name").execute()
        return [
            AvatarItem(id=str(row["id"]), imageUrl=row.get("image_url"), name=row.get("name"))
            for row in result.data
        ]
