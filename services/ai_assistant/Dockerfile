# Same structure as HTTP API Dockerfile -- only paths and port differ.
# See services/http_api/Dockerfile for detailed comments on each line.
FROM python:3.12-slim

WORKDIR /app

# Layer 1: Shared package (changes rarely)
COPY pyproject.toml .
COPY shared/ ./shared/
RUN pip install --no-cache-dir -e .

# Layer 2: Service dependencies (changes rarely)
# This one also installs google-genai for the AI chat feature
COPY services/ai_assistant/requirements.txt ./services/ai_assistant/
RUN pip install --no-cache-dir -r services/ai_assistant/requirements.txt

# Layer 3: Service code (changes often -- last for cache efficiency)
COPY services/ai_assistant/app/ ./services/ai_assistant/app/

# Switch to service directory so "from app.routers import chat" works
WORKDIR /app/services/ai_assistant

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
