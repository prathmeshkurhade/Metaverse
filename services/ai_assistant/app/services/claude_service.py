"""
Gemini Service -- handles AI chat using Google's Gemini API.

WHY Gemini instead of Claude?
Gemini has a free tier -- no cost for learning. The architecture stays
exactly the same: fetch room context, build system prompt, call AI, store
messages. Swapping the AI provider is just changing one API call.

ARCHITECTURE (unchanged):
1. User sends a message + space_id
2. We fetch room context (name, elements, user count) from Supabase
3. We build a system prompt with room context
4. We send the conversation to Gemini
5. We store the message + response in Supabase (room_messages table)
6. We return the AI response
"""

from google import genai

from shared.config import settings
from shared.database import supabase


class ClaudeService:
    # WHY keep the class name "ClaudeService"?
    # The router imports ClaudeService by name. Renaming it would mean changing
    # the router too. The name is just a label -- what matters is what it does.
    # In Docker/k8s phases we can rename if we want, but no reason to break
    # imports for a cosmetic change right now.

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def chat(
        self, space_id: str, user_id: str, message: str
    ) -> str:
        """
        Send a message to the AI and get a response.

        Steps:
        1. Get room context from Supabase (space name, elements, etc.)
        2. Get recent chat history for this room
        3. Build the conversation with a system prompt
        4. Call Gemini API
        5. Store both messages in DB
        6. Return the AI response
        """
        # 1. Get room context
        context = await self._get_room_context(space_id)

        # 2. Get recent chat history (last 20 messages for context window)
        history = await self._get_chat_history(space_id, limit=20)

        # 3. Build the system prompt
        system_prompt = self._build_system_prompt(context)

        # 4. Build conversation messages
        # WHY this format? Gemini expects {"role": "user"/"model", "parts": [{"text": "..."}]}
        # Note: Gemini uses "model" where Anthropic uses "assistant"
        contents = []
        for msg in history:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        contents.append({"role": "user", "parts": [{"text": message}]})

        # 5. Call Gemini API
        response = self.client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=contents,
            config={
                "system_instruction": system_prompt,
                "max_output_tokens": settings.GEMINI_MAX_TOKENS,
            },
        )

        ai_response = response.text

        # 6. Store both messages in DB
        supabase.table("room_messages").insert([
            {
                "space_id": space_id,
                "user_id": user_id,
                "role": "user",
                "content": message,
            },
            {
                "space_id": space_id,
                "user_id": None,  # AI messages have no user_id
                "role": "assistant",
                "content": ai_response,
            },
        ]).execute()

        return ai_response

    async def get_history(self, space_id: str, limit: int = 50) -> list[dict]:
        """Get chat history for a room."""
        return await self._get_chat_history(space_id, limit)

    async def _get_room_context(self, space_id: str) -> dict:
        """Fetch room context for the AI's system prompt."""
        space = (
            supabase.table("spaces")
            .select("name, width, height")
            .eq("id", space_id)
            .execute()
        )
        if not space.data:
            return {"name": "Unknown Room", "width": 0, "height": 0, "elements": []}

        space_data = space.data[0]

        elements = (
            supabase.table("space_elements")
            .select("element_id, x, y, elements(name, image_url)")
            .eq("space_id", space_id)
            .execute()
        )

        return {
            "name": space_data["name"],
            "width": space_data["width"],
            "height": space_data["height"],
            "elements": elements.data,
        }

    async def _get_chat_history(self, space_id: str, limit: int) -> list[dict]:
        """Fetch recent chat messages for a room, ordered chronologically."""
        result = (
            supabase.table("room_messages")
            .select("role, content, created_at")
            .eq("space_id", space_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        return result.data

    def _build_system_prompt(self, context: dict) -> str:
        """Build the AI's system prompt with room context."""
        element_desc = "No elements placed yet."
        if context.get("elements"):
            items = []
            for el in context["elements"]:
                name = el.get("elements", {}).get("name", "Unknown") if el.get("elements") else "Object"
                items.append(f"- {name} at position ({el['x']}, {el['y']})")
            element_desc = "\n".join(items)

        return f"""You are the AI assistant for a 2D metaverse room called "{context['name']}".

Room details:
- Dimensions: {context['width']}x{context['height']} grid units
- Elements in the room:
{element_desc}

Your role:
- Help users navigate and understand the room
- Answer questions about what's in the room
- Be friendly, concise, and helpful
- Keep responses short (1-3 sentences) since this is a chat interface
- You can describe the room layout and suggest where users might want to explore
- If asked about things outside the room, politely redirect to room-related topics"""
