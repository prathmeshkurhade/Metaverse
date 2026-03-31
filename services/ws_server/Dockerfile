# Same structure as HTTP API Dockerfile -- only paths and port differ.
# See services/http_api/Dockerfile for detailed comments on each line.
FROM python:3.12-slim

WORKDIR /app

# Layer 1: Shared package (changes rarely)
COPY pyproject.toml .
COPY shared/ ./shared/
RUN pip install --no-cache-dir -e .

# Layer 2: Service dependencies (changes rarely)
COPY services/ws_server/requirements.txt ./services/ws_server/
RUN pip install --no-cache-dir -r services/ws_server/requirements.txt

# Layer 3: Service code (changes often -- last for cache efficiency)
COPY services/ws_server/app/ ./services/ws_server/app/

# Switch to service directory so "from app.room_manager import ..." works
WORKDIR /app/services/ws_server

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
