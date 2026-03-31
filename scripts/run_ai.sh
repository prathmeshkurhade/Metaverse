#!/bin/bash
# Run the AI Assistant service (Microservice 3) on port 8002

cd "$(dirname "$0")/.." || exit 1
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "Starting AI Assistant on port 8002..."
echo "API docs: http://localhost:8002/docs"
echo ""

cd services/ai_assistant
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
