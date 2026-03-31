#!/bin/bash
# Run the WebSocket server (Microservice 2) on port 8001

cd "$(dirname "$0")/.." || exit 1
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "Starting WebSocket Server on port 8001..."
echo ""

cd services/ws_server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
