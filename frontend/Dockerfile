# ══════════════════════════════════════════════════════════
# STAGE 1: Build the React app
# ══════════════════════════════════════════════════════════
# WHY "AS builder"? This names the stage so we can reference it later.
# Everything in this stage is THROWN AWAY after the build finishes.
# Only the build output (dist/) survives into stage 2.
FROM node:20-slim AS builder

WORKDIR /app

# Copy package.json first (same caching trick as Python services)
# npm install only re-runs if package.json changes
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# Now copy the rest of the frontend code and build
COPY frontend/ .
RUN npm run build
# After this, /app/dist/ contains index.html + JS bundles + CSS
# That's ALL we need. Node.js (200MB) is no longer needed.

# ══════════════════════════════════════════════════════════
# STAGE 2: Serve with Nginx
# ══════════════════════════════════════════════════════════
# WHY start fresh from nginx:alpine?
# Alpine is a tiny Linux (~5MB). The final image is ~25MB total.
# If we kept the Node stage, the image would be ~250MB for no reason.
FROM nginx:alpine

# Copy the built files from stage 1 into Nginx's default serve directory
# --from=builder means "copy from the stage named 'builder'"
COPY --from=builder /app/dist /usr/share/nginx/html

# Replace Nginx's default config with our custom one that handles
# API proxying and React Router
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Nginx runs automatically when the container starts (built into the base image)
# No CMD needed -- nginx:alpine's default CMD is "nginx -g 'daemon off;'"
