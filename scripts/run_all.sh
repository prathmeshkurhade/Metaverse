#!/bin/bash
# ============================================================
# Run ALL services in the background (for local development)
#
# Usage:
#   ./scripts/run_all.sh       # Start all 3 services
#   ./scripts/run_all.sh stop  # Stop all 3 services
#
# WHY background processes?
# In production, Docker Compose handles this. For local dev without Docker,
# we run each service as a background process. The PIDs are saved to .pid
# files so we can stop them later.
#
# NOTE: For the frontend, run `cd frontend && npm run dev` separately.
# ============================================================

cd "$(dirname "$0")/.." || exit 1
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

PIDS_DIR=".pids"
mkdir -p "$PIDS_DIR"

stop_services() {
    echo "Stopping services..."
    for pidfile in "$PIDS_DIR"/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            kill "$pid" 2>/dev/null && echo "Stopped PID $pid ($(basename "$pidfile" .pid))"
            rm "$pidfile"
        fi
    done
    echo "All services stopped."
}

if [ "$1" = "stop" ]; then
    stop_services
    exit 0
fi

# Stop any existing services first
stop_services 2>/dev/null

echo "Starting all services..."
echo ""

# HTTP API (port 8000)
cd services/http_api
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
echo $! > "../../$PIDS_DIR/http_api.pid"
cd ../..
echo "  HTTP API:     http://localhost:8000  (docs: http://localhost:8000/docs)"

# WebSocket Server (port 8001)
cd services/ws_server
uvicorn app.main:app --host 0.0.0.0 --port 8001 &
echo $! > "../../$PIDS_DIR/ws_server.pid"
cd ../..
echo "  WebSocket:    ws://localhost:8001"

# AI Assistant (port 8002)
cd services/ai_assistant
uvicorn app.main:app --host 0.0.0.0 --port 8002 &
echo $! > "../../$PIDS_DIR/ai_assistant.pid"
cd ../..
echo "  AI Assistant: http://localhost:8002  (docs: http://localhost:8002/docs)"

echo ""
echo "All services started! Run './scripts/run_all.sh stop' to stop."
echo "For the frontend: cd frontend && npm install && npm run dev"
