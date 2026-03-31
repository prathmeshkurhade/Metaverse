# Metaverse FastAPI - DevOps Learning Project

## What this is
A 2D Metaverse app rebuilt in FastAPI (from a TypeScript/Turborepo original) as a hands-on DevOps learning project. The user wants to learn DevOps by deploying this app end-to-end on AWS.

## Architecture
3 microservices + 1 frontend:
- **HTTP API** (`services/http_api/`, port 8000) -- CRUD REST API (auth, spaces, admin)
- **WebSocket Server** (`services/ws_server/`, port 8001) -- real-time room movement
- **AI Room Assistant** (`services/ai_assistant/`, port 8002) -- Claude-powered chatbot per room
- **Frontend** (`frontend/`) -- React/Vite minimal UI

Shared code in `shared/` (config, database, auth, models). Database: Supabase PostgreSQL.

## Current Status
- **Phase 1: COMPLETE** -- All 3 services built, frontend built, tests written, SQL schema ready
- **Phase 2: Docker** -- NEXT (see DEVOPS_PLAN.md for full 41-task plan)
- Phases 3-7 pending: AWS, CI/CD, k3s Kubernetes, Monitoring, Security

## How to teach this user
- They know FastAPI well (from their Infinity project)
- Docker/AWS/K8s newbie -- explain EVERYTHING, every flag, every line
- Every line of code must have a WHY explanation
- They want deep conceptual understanding, not copy-paste
- Casual communication style
- Budget: AWS free tier only ($0/month)
- They have a domain name
- Full plan with all 41 tasks: see `DEVOPS_PLAN.md`

## Key patterns (reused from their Infinity project)
- Pydantic BaseSettings for config (`shared/config.py`)
- Supabase client with anon + admin separation (`shared/database.py`)
- JWT auth with bcrypt (`shared/auth/dependencies.py`)
- Router -> Service -> DB query layer pattern

## Running locally
1. Run SQL from `supabase_schema.sql` in Supabase SQL Editor
2. Copy `.env.example` to `.env`, fill in Supabase + Anthropic keys
3. `pip install -e . && pip install -r services/http_api/requirements.txt`
4. 3 terminals: `scripts\run_http.bat`, `scripts\run_ws.bat`, `scripts\run_ai.bat`
5. Frontend: `cd frontend && npm install && npm run dev`
