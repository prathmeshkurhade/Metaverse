"""
AI Room Assistant Microservice -- Claude-powered chatbot for metaverse rooms.

Users can chat with an AI assistant within any room. The AI knows about
the room's context (name, elements, number of users) and can answer
questions about the space.

WHY a separate microservice?
1. AI API calls are SLOW (1-5 seconds) compared to CRUD operations (10-50ms).
   If this ran in the HTTP API, a flood of AI requests would slow down
   all CRUD operations for everyone.
2. AI has its own rate limits (Anthropic API). Isolating it means rate
   limit issues don't cascade to other services.
3. Different scaling needs: you might need 3 HTTP API instances but only
   1 AI instance (AI is expensive, so you want to control costs).
4. Different environment: needs ANTHROPIC_API_KEY, which the other services don't.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat

app = FastAPI(
    title="Metaverse AI Assistant",
    description="Claude-powered room chatbot",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1/ai", tags=["ai"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ai-assistant"}
