#!/bin/bash
# ============================================================
# Run the test suite
#
# PREREQUISITE: Both HTTP API and WebSocket server must be running!
#   Terminal 1: ./scripts/run_http.sh
#   Terminal 2: ./scripts/run_ws.sh
#   Terminal 3: ./scripts/run_tests.sh
#
# WHY not start servers in this script?
# Tests run against LIVE servers (integration tests, not unit tests).
# Starting/stopping servers in the test script would add complexity
# and make debugging harder. Keep it simple -- start servers, then test.
# ============================================================

cd "$(dirname "$0")/.." || exit 1
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "Running tests..."
echo "Make sure HTTP API (port 8000) and WS Server (port 8001) are running!"
echo ""

pytest tests/ -v --tb=short
