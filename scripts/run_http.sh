#!/bin/bash
# ============================================================
# Run the HTTP API service (Microservice 1)
#
# WHY uvicorn with these flags?
# --host 0.0.0.0: Accept connections from any interface (not just localhost)
#   This is needed when running in Docker later.
# --port 8000: The port this service listens on
# --reload: Watch for file changes and auto-restart (DEV ONLY, never in production)
#   In production, remove --reload for stability and performance.
# ============================================================

cd "$(dirname "$0")/.." || exit 1

# Ensure shared package is importable
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "Starting HTTP API on port 8000..."
echo "Swagger docs: http://localhost:8000/docs"
echo ""

cd services/http_api
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
