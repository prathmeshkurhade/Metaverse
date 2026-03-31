"""
Admin service -- business logic for managing elements, avatars, and maps.
"""

from shared.database import supabase
from shared.models.element import MapDefaultElement


class AdminService:
    async def create_element(
        self, image_url: str, width: int, height: int, static: bool
    ) -> str:
        """
        Create a new element type.

        WHY store width/height on the element?
        Elements have intrinsic dimensions. When placed in a space, they
        occupy width*height grid cells. This is used for collision detection
        and rendering on the frontend.
        """
        result = (
            supabase.table("elements")
            .insert({
                "image_url": image_url,
                "width": width,
                "height": height,
                "static": static,
            })
            .execute()
        )
        return str(result.data[0]["id"])

    async def update_element(self, element_id: str, image_url: str) -> None:
        """Update an element's image URL."""
        result = (
            supabase.table("elements")
            .update({"image_url": image_url})
            .eq("id", element_id)
            .execute()
        )
        if not result.data:
            raise ValueError("Element not found")

    async def create_avatar(self, image_url: str, name: str) -> str:
        """Create a new avatar option."""
        result = (
            supabase.table("avatars")
            .insert({
                "image_url": image_url,
                "name": name,
            })
            .execute()
        )
        return str(result.data[0]["id"])

    async def create_map(
        self,
        thumbnail: str,
        dimensions: str,
        name: str,
        default_elements: list[MapDefaultElement],
    ) -> str:
        """
        Create a map template with default elements.

        Steps:
        1. Parse dimensions "100x200" into width=100, height=200
        2. Insert the map record
        3. Insert all default elements linked to this map

        WHY two inserts (map + map_elements) instead of one?
        Relational database design. The map table stores the map's properties.
        The map_elements table stores the many-to-many relationship between
        maps and elements (with position data). This is normalized design --
        no data duplication, easy to query.
        """
        # Parse dimensions
        try:
            parts = dimensions.lower().split("x")
            width, height = int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            raise ValueError(f"Invalid dimensions: {dimensions}")

        # Create the map
        map_result = (
            supabase.table("maps")
            .insert({
                "thumbnail": thumbnail,
                "width": width,
                "height": height,
                "name": name,
            })
            .execute()
        )
        map_id = str(map_result.data[0]["id"])

        # Insert default elements (if any)
        if default_elements:
            elements_data = [
                {
                    "map_id": map_id,
                    "element_id": el.elementId,
                    "x": el.x,
                    "y": el.y,
                }
                for el in default_elements
            ]
            supabase.table("map_elements").insert(elements_data).execute()

        return map_id
