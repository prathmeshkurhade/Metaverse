"""
Space service -- business logic for room CRUD and element placement.

The most complex service because spaces involve:
- Creating rooms with optional map templates
- Copying default elements from maps to new spaces
- Validating element positions against room dimensions
- Ownership checks for deletion
"""

from shared.database import supabase
from shared.models.space import SpaceDetailResponse, SpaceElement, SpaceListItem


def parse_dimensions(dimensions: str) -> tuple[int, int]:
    """
    Parse "100x200" into (100, 200).

    WHY a helper function?
    Dimensions come as strings from the API ("100x200"). We need integers
    to validate element positions. This parsing happens in multiple places
    (create space, add element), so extracting it avoids duplication.
    """
    try:
        parts = dimensions.lower().split("x")
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        raise ValueError(f"Invalid dimensions format: {dimensions}. Expected 'WIDTHxHEIGHT'")


class SpaceService:
    async def create_space(
        self,
        name: str,
        dimensions: str | None,
        map_id: str | None,
        creator_id: str,
        is_public: bool = False,
    ) -> str:
        """
        Create a new space, optionally from a map template.

        LOGIC:
        1. If mapId provided: fetch the map, use its dimensions, copy its default elements
        2. If no mapId: dimensions must be provided, space starts empty
        3. If neither mapId nor dimensions: error

        WHY copy elements from map instead of referencing?
        Each space needs its own element instances so users can add/remove
        elements from their space without affecting the template or other spaces.
        This is the "template pattern" -- the map is a blueprint, the space is a copy.
        """
        width, height = None, None

        if map_id:
            # Fetch map to get dimensions and default elements
            map_result = (
                supabase.table("maps")
                .select("id, width, height, thumbnail")
                .eq("id", map_id)
                .execute()
            )
            if not map_result.data:
                raise ValueError("Map not found")

            map_data = map_result.data[0]
            width = map_data["width"]
            height = map_data["height"]
            dimensions = f"{width}x{height}"
        elif dimensions:
            width, height = parse_dimensions(dimensions)
        else:
            raise ValueError("Either mapId or dimensions must be provided")

        # Create the space
        space_result = (
            supabase.table("spaces")
            .insert({
                "name": name,
                "width": width,
                "height": height,
                "creator_id": creator_id,
                "map_id": map_id,
                "is_public": is_public,
            })
            .execute()
        )
        space_id = space_result.data[0]["id"]

        # If created from a map, copy the default elements into this space
        if map_id:
            map_elements = (
                supabase.table("map_elements")
                .select("element_id, x, y")
                .eq("map_id", map_id)
                .execute()
            )
            if map_elements.data:
                # Batch insert all default elements into the new space
                space_elements = [
                    {
                        "space_id": space_id,
                        "element_id": el["element_id"],
                        "x": el["x"],
                        "y": el["y"],
                    }
                    for el in map_elements.data
                ]
                supabase.table("space_elements").insert(space_elements).execute()

        return space_id

    async def delete_space(self, space_id: str, user_id: str) -> None:
        """
        Delete a space. Only the creator can delete it.

        WHY ownership check?
        Without it, any authenticated user could delete anyone's space.
        The test spec explicitly tests that user A can't delete user B's space.
        """
        # Find the space
        space = (
            supabase.table("spaces")
            .select("id, creator_id")
            .eq("id", space_id)
            .execute()
        )
        if not space.data:
            raise ValueError("Space not found")

        if space.data[0]["creator_id"] != user_id:
            raise PermissionError("Not the owner")

        # Delete space elements first (foreign key constraint), then the space
        supabase.table("space_elements").delete().eq("space_id", space_id).execute()
        supabase.table("spaces").delete().eq("id", space_id).execute()

    async def list_spaces(self, user_id: str) -> list[SpaceListItem]:
        """List all spaces owned by a user."""
        result = (
            supabase.table("spaces")
            .select("id, name, width, height, thumbnail, is_public")
            .eq("creator_id", user_id)
            .execute()
        )
        return [
            SpaceListItem(
                id=row["id"],
                name=row["name"],
                dimensions=f"{row['width']}x{row['height']}",
                thumbnail=row.get("thumbnail"),
                isPublic=row.get("is_public", False),
            )
            for row in result.data
        ]

    async def list_public_spaces(self) -> list[SpaceListItem]:
        """List all public spaces from all users."""
        result = (
            supabase.table("spaces")
            .select("id, name, width, height, thumbnail, is_public, creator_id, users(username)")
            .eq("is_public", True)
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        return [
            SpaceListItem(
                id=row["id"],
                name=row["name"],
                dimensions=f"{row['width']}x{row['height']}",
                thumbnail=row.get("thumbnail"),
                isPublic=True,
                creatorName=row.get("users", {}).get("username") if row.get("users") else None,
            )
            for row in result.data
        ]

    async def get_space(self, space_id: str) -> SpaceDetailResponse:
        """
        Get a space's details and all its placed elements.

        WHY two queries?
        One for the space (to get dimensions), one for its elements.
        We could use a Supabase join, but two simple queries are clearer
        and easier to debug. The performance difference is negligible for
        the number of elements we're dealing with (< 100 per space).
        """
        # Get the space
        space = (
            supabase.table("spaces")
            .select("id, width, height")
            .eq("id", space_id)
            .execute()
        )
        if not space.data:
            raise ValueError("Space not found")

        space_data = space.data[0]

        # Get all elements in this space
        elements = (
            supabase.table("space_elements")
            .select("id, element_id, x, y")
            .eq("space_id", space_id)
            .execute()
        )

        return SpaceDetailResponse(
            dimensions=f"{space_data['width']}x{space_data['height']}",
            elements=[
                SpaceElement(
                    id=str(el["id"]),
                    elementId=str(el["element_id"]),
                    x=el["x"],
                    y=el["y"],
                )
                for el in elements.data
            ],
        )

    async def add_element(
        self, space_id: str, element_id: str, x: int, y: int
    ) -> None:
        """
        Place an element at a position in a space.

        Validates that the position is within the space's dimensions.

        WHY validate position?
        Without validation, you could place an element at x=99999 in a 100x200 room.
        The test spec explicitly tests this boundary check.
        """
        # Get space dimensions
        space = (
            supabase.table("spaces")
            .select("width, height")
            .eq("id", space_id)
            .execute()
        )
        if not space.data:
            raise ValueError("Space not found")

        width = space.data[0]["width"]
        height = space.data[0]["height"]

        # Validate position is within bounds
        if x < 0 or x >= width or y < 0 or y >= height:
            raise ValueError(
                f"Position ({x}, {y}) is outside space dimensions ({width}x{height})"
            )

        # Insert the element placement
        supabase.table("space_elements").insert({
            "space_id": space_id,
            "element_id": element_id,
            "x": x,
            "y": y,
        }).execute()

    async def delete_element(self, space_element_id: str) -> None:
        """Remove an element instance from a space."""
        result = (
            supabase.table("space_elements")
            .delete()
            .eq("id", space_element_id)
            .execute()
        )
        if not result.data:
            raise ValueError("Space element not found")
