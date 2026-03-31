# ── Base image ──
# python:3.12-slim is a minimal Linux (~150MB) with Python pre-installed.
# WHY slim? The full image is ~900MB. Slim removes docs, man pages, and
# rarely-used tools. Our app doesn't need any of that.
FROM python:3.12-slim

# ── Working directory ──
# Create /app inside the container and cd into it.
# All COPY and RUN commands after this happen inside /app.
WORKDIR /app

# ── Layer 1: Install shared package (changes rarely) ──
# WHY copy pyproject.toml + shared/ first?
# Docker caches each step as a "layer". If the files in a COPY haven't changed,
# Docker skips that layer AND all layers after it (until one changes).
# The shared package changes rarely, so this layer stays cached most of the time.
COPY pyproject.toml .
COPY shared/ ./shared/
RUN pip install --no-cache-dir -e .

# ── Layer 2: Install service dependencies (changes rarely) ──
# Same caching trick: requirements.txt only changes when you add/remove a package.
# --no-cache-dir: don't save pip's download cache (saves ~50MB, useless in a container)
COPY services/http_api/requirements.txt ./services/http_api/
RUN pip install --no-cache-dir -r services/http_api/requirements.txt

# ── Layer 3: Copy service code (changes often) ──
# This is LAST because your code changes on every edit. Layers above stay cached.
COPY services/http_api/app/ ./services/http_api/app/

# ── Switch to service directory ──
# WHY? The code does "from app.routers import auth, space, ..."
# Python looks for "app/" relative to the CURRENT directory.
# Without this, Python is in /app (project root) and can't find app.routers.
# This is the same thing the bat scripts do: "cd services\http_api" before running.
WORKDIR /app/services/http_api

EXPOSE 8000

# Now uvicorn can use "app.main:app" (simple) instead of "services.http_api.app.main:app"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
