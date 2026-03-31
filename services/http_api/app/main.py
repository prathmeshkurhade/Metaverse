"""
HTTP API Microservice -- the main CRUD REST API for the 2D Metaverse.

This is the central service that handles:
- Authentication (signup/signin)
- User metadata (avatar selection)
- Space CRUD (create, read, delete rooms)
- Admin operations (manage elements, avatars, maps)

WHY FastAPI?
FastAPI is async-native, has automatic OpenAPI docs, and uses Pydantic for
request/response validation. It's what you already know from Infinity.

WHY a separate main.py per service?
Each microservice is its own FastAPI app with its own process. This means:
- They can be deployed independently (different Docker containers)
- They can scale independently (3 HTTP API instances, 1 WebSocket instance)
- A crash in one doesn't bring down the others (fault isolation)

STARTUP FLOW:
1. Python imports this module
2. FastAPI creates the app instance
3. Routers are registered (each router = a group of related endpoints)
4. Uvicorn starts the ASGI server on port 8000
5. Requests come in -> FastAPI routes them to the correct handler
"""

import sys
from pathlib import Path

# WHY this sys.path hack?
# The shared package is at ../../shared relative to this file.
# In production (Docker), we install it properly via pip install -e .
# In local dev, this hack lets us run the service directly without installing.
# It adds the project root to Python's module search path.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import admin, auth, space, user

# ─── Create the FastAPI app ───
app = FastAPI(
    title="Metaverse HTTP API",
    description="CRUD REST API for the 2D Metaverse",
    version="0.1.0",
)

# ─── CORS Middleware ───
# WHY CORS?
# Your React frontend runs on localhost:3000, but the API runs on localhost:8000.
# Browsers block cross-origin requests by default (security feature).
# CORS headers tell the browser "it's OK, this origin is allowed."
# In production, replace "*" with your actual domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routers ───
# Each router handles a group of related endpoints.
# The prefix means all routes in auth.router start with /api/v1
# (e.g., /api/v1/signup, /api/v1/signin)
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(user.router, prefix="/api/v1", tags=["user"])
app.include_router(space.router, prefix="/api/v1", tags=["space"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])


# ─── Health Check ───
# WHY a health check?
# Docker, Kubernetes, and load balancers ping this endpoint to know if the
# service is alive. If it returns non-200, the orchestrator restarts the container.
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "http-api"}
