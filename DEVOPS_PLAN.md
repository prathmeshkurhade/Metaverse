 # DevOps Mastery: 2D Metaverse in FastAPI - Complete Learning Plan

## Context

You have a scaffolded 2D Metaverse app (TypeScript/Turborepo) with comprehensive test specs but empty implementations. You also have production FastAPI experience from Infinity (Supabase, JWT auth, AI integrations). The goal: rebuild the metaverse in FastAPI as 3 microservices, then learn DevOps end-to-end by deploying it on AWS -- Docker, CI/CD, Kubernetes (k3s), monitoring, security. Every line of code explained. Budget: $0 (AWS free tier + existing credits).

---

## Project Structure

Fresh repo: `metaverse-fastapi/` (NOT inside the existing turborepo)

```
metaverse-fastapi/
  shared/                     # Shared Python package (auth, models, config, db)
    __init__.py
    config.py                 # Pydantic BaseSettings (reuse Infinity pattern)
    database.py               # Supabase client
    auth/
      dependencies.py         # JWT validation (custom HS256, not Supabase Auth)
    models/
      user.py, space.py, element.py
  services/
    http_api/                 # Microservice 1: CRUD REST API
      app/
        main.py
        routers/              # auth, user, space, admin, elements
        services/             # Business logic layer
      requirements.txt
      Dockerfile
    ws_server/                # Microservice 2: Real-time WebSocket
      app/
        main.py
        room_manager.py       # Connection tracking, broadcasts, movement validation
      requirements.txt
      Dockerfile
    ai_assistant/             # Microservice 3: AI Room Chatbot (Claude API)
      app/
        main.py
        routers/chat.py
        services/claude_service.py
      requirements.txt
      Dockerfile
  frontend/                   # Minimal React (Vite) - NOT the focus
    Dockerfile
  nginx/
    nginx.conf
  k8s/                        # Kubernetes manifests (Phase 5)
  monitoring/                 # Prometheus + Grafana configs (Phase 6)
  .github/workflows/          # CI/CD pipelines (Phase 4)
  docker-compose.yml
  docker-compose.dev.yml
  docker-compose.prod.yml
  tests/                      # Pytest integration tests
  pyproject.toml
  .env.example
```

---

## Phase 1: Build the Application (8 Tasks)

**Goal**: 3 working microservices + frontend running locally. You know FastAPI, so this is about translating the existing test spec into Python.

### Task 1.1: Initialize project structure and shared package
- Create directory structure above
- `pyproject.toml` at root with shared package installable via `pip install -e .`
- `shared/config.py` -- Pydantic `BaseSettings` with `SettingsConfigDict` (exact pattern from [config.py](file:///C:/Users/ADMIN/OneDrive/Desktop/Infinity-Main/Infinity/backend/app/config.py))
- Variables: SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY, JWT_SECRET, ANTHROPIC_API_KEY
- **Why shared package**: All 3 services import `from shared.auth import get_current_user`. One change propagates everywhere. Each Dockerfile copies `shared/` in.

### Task 1.2: Set up Supabase database schema
- Tables: users, avatars, maps, map_elements, elements, spaces, space_elements, user_metadata, room_messages (for AI chat)
- Schema derived from test spec at `metaverse/tests/index.test.js` (1039 lines of integration tests = complete API contract)
- **Why Supabase hosted**: No database server to manage = entire category of DevOps eliminated

### Task 1.3: Build shared auth module
- `shared/database.py` -- Supabase client (reuse Infinity pattern: anon + admin clients)
- `shared/auth/dependencies.py` -- Custom JWT auth (NOT Supabase Auth, since test spec uses username/password signup)
  - bcrypt password hashing
  - python-jose HS256 JWT signing
  - `get_current_user` and `get_admin_user` FastAPI dependencies
- **Why custom auth**: Test spec requires username-based auth with admin/user roles. Understanding every JWT piece matters for Nginx headers + K8s secrets later.

### Task 1.4: Build Microservice 1 -- HTTP API (FastAPI)
- `main.py` with lifespan, middleware stack (reuse Infinity patterns: CORS, rate limiter, security headers, logging)
- Routers: auth (signup/signin), user (metadata), space (CRUD + elements), admin (elements/avatars/maps)
- Service layer pattern: router -> service -> Supabase query (same as Infinity)
- All endpoints match test spec exactly

### Task 1.5: Build Microservice 2 -- WebSocket Server
- FastAPI WebSocket endpoint at `/ws`
- `RoomManager` class: tracks users per space, positions, WebSocket connections
- Protocol: join -> space-joined (spawn + existing users) -> move -> movement/movement-rejected -> user-left on disconnect
- Movement validation: max 1 unit per message, within space boundaries
- **Why separate service**: WebSockets hold long-lived connections with completely different scaling characteristics. This is the real reason for microservices -- independent scaling.

### Task 1.6: Build Microservice 3 -- AI Room Assistant
- `POST /api/v1/ai/chat` -- send message, get Claude response with room context
- `GET /api/v1/ai/history/{space_id}` -- chat history per room
- Uses Anthropic Claude API (you already use it in Infinity)
- System prompt includes room context: name, user count, elements present
- Stores conversation in `room_messages` Supabase table
- **Why this AI feature**: Legitimate 3rd microservice with its own API, external API calls, own env vars, own scaling needs. Not contrived.

### Task 1.7: Build minimal React frontend
- Vite + React. Login/signup, space list, 2D canvas (grid + elements + avatars), chat sidebar
- Connects to all 3 services. Keeps things minimal -- exists to test backends, not to be production UI.

### Task 1.8: Run locally and write pytest tests
- Port test logic from `tests/index.test.js` to Python pytest with `httpx.AsyncClient` + `websockets`
- Get all 3 services running locally (3 terminals, 3 ports)
- **Why test before Docker**: Known-good local state. If something breaks after Docker, you know it's Docker, not your code.

---

## Phase 2: Docker (6 Tasks)

**Goal**: Deep container understanding, then containerize everything with optimized Dockerfiles + Docker Compose orchestration.

### Task 2.1: Docker fundamentals -- what containers actually are
- Install Docker Desktop
- Hands-on: `docker run -it python:3.12-slim bash`, `docker ps`, `docker exec`, `docker logs`, `docker stop/rm`
- **Concepts**: Containers vs VMs (kernel sharing, not virtualization), namespaces (PID, network, mount), cgroups (resource limits), images vs containers (class vs instance), layers (union filesystem)

### Task 2.2: Write Dockerfiles for each service
- Multi-stage builds: Stage 1 (builder) installs deps, Stage 2 (runtime) copies only what's needed
- Why `--no-cache-dir` (no future installs in container), why `0.0.0.0` (accept connections from outside container namespace), why `COPY requirements.txt` before `COPY .` (layer caching)
- Frontend: node:20-slim builds -> nginx:alpine serves static
- Target: <150MB per Python service image

### Task 2.3: Docker networking deep dive
- Manual: `docker network create`, run 2 containers, `curl http://container-name:port` between them
- **Key concept**: Docker DNS resolves container names on shared networks. This is the foundation for K8s service discovery later.

### Task 2.4: Docker Compose for local orchestration
- `docker-compose.yml` with all 4 services + health checks + `depends_on` with conditions
- Essential commands: `up --build`, `down`, `logs -f`, `ps`
- **Why healthchecks**: `depends_on: condition: service_healthy` prevents AI service from crashing because HTTP API isn't ready yet (startup ordering problem)

### Task 2.5: Volumes and dev workflow
- `docker-compose.dev.yml` override with bind mounts + `--reload` for hot-reloading
- **Key concept**: Dev uses volumes (mount code in), prod bakes code into image (immutability). Never volume-mount in production.

### Task 2.6: Image optimization and .dockerignore
- `.dockerignore`: node_modules, venv, .git, __pycache__, .env
- `docker images` to check sizes, `docker history` for layer analysis
- **Why it matters**: t3.micro has 8GB disk. 500MB images = out of disk after 5 deploys.

---

## Phase 3: AWS Foundations + Manual Deployment (7 Tasks)

**Goal**: Deploy manually first so you understand exactly what CI/CD automates later. Every manual step becomes a CI pipeline step.

### Task 3.1: AWS account setup and cost protection
- Enable Billing Alerts in CloudWatch ($1, $5, $10 thresholds)
- Create AWS Budget ($5/month limit with email alerts)
- Create IAM user (never use root for CLI)
- Install + configure AWS CLI
- **Critical**: Billing alert is your safety net against surprise charges

### Task 3.2: Launch EC2 instance
- t3.micro, Ubuntu 24.04 LTS, key pair (.pem)
- Security Group: SSH (22, your IP only), HTTP (80), HTTPS (443)
- Allocate Elastic IP (free while attached to running instance; $3.60/month if instance stopped!)
- SSH in: `ssh -i key.pem ubuntu@elastic-ip`

### Task 3.3: Install Docker on EC2 and deploy manually
- `sudo apt install docker.io docker-compose-v2`
- Clone repo, create `.env`, `docker compose up -d --build`
- Verify services via `http://elastic-ip:8000/health`
- **Why manual first**: If CI/CD breaks, you need to debug. Can't debug what you don't understand.

### Task 3.4: Nginx as reverse proxy
- Single entry point on port 80, routes by URL path:
  - `/` -> frontend
  - `/api/v1/` -> http-api
  - `/ws` -> ws-server (with WebSocket upgrade headers + 24h timeout)
  - `/api/v1/ai/` -> ai-assistant
- Add Nginx to Docker Compose, remove individual port exposures
- **Key details**: `proxy_set_header X-Real-IP` (so rate limiter sees real IPs), `proxy_http_version 1.1` + `Upgrade/Connection` headers (WebSocket handshake), `proxy_read_timeout 86400` (prevent WS disconnect)

### Task 3.5: Domain setup and DNS
- A record: `@` -> Elastic IP, `www` -> Elastic IP
- Use external registrar (NOT Route 53 -- $0.50/month per hosted zone, unnecessary cost)
- Verify: `dig yourdomain.com`

### Task 3.6: SSL with Let's Encrypt + Certbot
- Certbot Docker container for certificate generation
- Nginx config: listen 443 with cert, redirect 80 -> 443
- Auto-renewal cron
- **Why mandatory**: Browsers block `wss://` without HTTPS. JWT tokens in plaintext = stolen credentials.

### Task 3.7: Full end-to-end verification
- Test every feature through `https://yourdomain.com`: signup, spaces, WebSocket movement, AI chat
- Document every manual step -- this document becomes your CI/CD pipeline spec

---

## Phase 4: CI/CD with GitHub Actions (5 Tasks)

**Goal**: Push to main = automatic build, test, deploy. Zero manual intervention.

### Task 4.1: GitHub Actions fundamentals
- `.github/workflows/ci.yml`: trigger on push/PR
- Pipeline: lint (ruff) -> test (pytest) -> build (docker compose build)
- `needs` keyword creates dependency chain: lint gates test gates build
- **Concept**: 2000 free CI minutes/month on GitHub

### Task 4.2: Docker image build + push to Docker Hub
- Docker Hub account (free, 1 private repo)
- Build and push with `docker/build-push-action`
- Tag with git SHA + latest: `yourusername/metaverse-http:abc123`
- **Why SHA tags**: `latest` doesn't tell you which code is running. SHA = traceable to exact commit.

### Task 4.3: Automated deployment to EC2
- SSH into EC2 via `appleboy/ssh-action`, `docker compose pull`, `docker compose up -d`
- `docker image prune -f` after deploy (8GB disk fills fast)
- **Why "pull" deployment**: Push images to registry, server pulls them. Scales to multiple servers later.

### Task 4.4: Environment management
- `main` branch = production, `develop` = staging
- CI runs tests on both, deploys only from `main`
- **Pattern**: merge to main = deploy (GitOps-lite)

### Task 4.5: Rollback strategy
- `docker-compose.prod.yml` uses `image: user/service:${IMAGE_TAG:-latest}`
- Rollback: `IMAGE_TAG=old-sha docker compose up -d` (seconds, not minutes)

---

## Phase 5: Container Orchestration with k3s (6 Tasks)

**Goal**: Learn real Kubernetes on your EC2 instance for free. k3s is CNCF-certified K8s that runs in 512MB RAM. (EKS costs $72/month -- skip it.)

### Task 5.1: Why Kubernetes and why k3s
- Docker Compose limitations: no rolling updates, no horizontal scaling, no automatic rescheduling
- k3s = full Kubernetes API, 512MB RAM, single binary
- **Why not Docker Swarm**: Effectively abandoned. K8s won. k3s skills transfer to EKS/GKE/AKS in any job.

### Task 5.2: Install k3s on EC2
- `curl -sfL https://get.k3s.io | sh -`
- `kubectl get nodes` to verify
- Single-node K8s -- same manifests would work on a 100-node cluster

### Task 5.3: Core K8s objects -- Pods, Deployments, Services
- Create `k8s/` manifests for each microservice
- Deployment: replicas, readinessProbe (`/health`), resource requests/limits (128Mi-256Mi per service on 1GB RAM)
- Service: stable network endpoint via label selectors
- **Key concepts**: Deployment vs bare Pod (self-healing), readinessProbe (traffic only to ready pods), resource limits (prevent OOM on t3.micro)

### Task 5.4: Secrets and ConfigMaps
- `kubectl create secret generic metaverse-secrets --from-literal=KEY=value`
- Mount into pods via `envFrom: secretRef`
- **Why better than .env**: Access-controlled, not on filesystem, foundation for proper secrets management

### Task 5.5: Ingress (replaces Nginx)
- k3s ships Traefik as ingress controller
- Ingress resource: path-based routing (`/api/v1` -> http-api, `/ws` -> ws-server, `/api/v1/ai` -> ai-assistant)
- cert-manager for automatic Let's Encrypt SSL
- **Key concept**: You declare routing rules, controller makes it happen. Same declarative pattern as Deployments.

### Task 5.6: Update CI/CD for K8s deployment
- `kubectl set image deployment/http-api http-api=user/service:$SHA`
- `kubectl rollout status` waits until new pods are ready
- Rolling update: new pod starts, passes health check, old pod terminates. Zero downtime.

---

## Phase 6: Monitoring & Observability (4 Tasks)

**Goal**: See what's happening inside your running system. Dashboards + alerts.

### Task 6.1: Structured logging and health checks
- JSON formatter for Python logging (timestamp, level, service, path, status_code)
- Deep health checks: `/health` actually pings Supabase, returns 503 if unreachable
- **Why JSON logs**: 3 services = interleaved logs. JSON is parseable. Foundation for log aggregation.

### Task 6.2: Prometheus for metrics
- Add `prometheus-fastapi-instrumentator` to each service (exposes `/metrics`)
- Deploy Prometheus in k3s with ConfigMap for scrape targets
- **Concept**: Prometheus pulls (scrapes) metrics every 15s. If scrape fails = service is down.

### Task 6.3: Grafana dashboards
- Connect Grafana to Prometheus
- Dashboards: request rate, response time (p50/p95/p99), error rate, active WebSocket connections, AI response time, CPU/memory
- **Golden signals**: latency, traffic, errors, saturation. These 4 metrics catch most problems.

### Task 6.4: Alerting
- Grafana alerts: error rate >5% for 5min, p95 latency >2s, health check failing 2min, CPU >80% for 10min
- Email notifications
- **Why thresholds aren't 0%**: Some errors are normal (bad input, rate limits). Alerting on every error = alert fatigue = ignoring alerts.

---

## Phase 7: Security Hardening (5 Tasks)

**Goal**: Secure every layer -- containers, network, secrets, application.

### Task 7.1: Docker security
- Non-root containers (`USER 1000` in Dockerfile)
- Read-only filesystem in k8s (`readOnlyRootFilesystem: true`)
- Image vulnerability scanning (`docker scout cves`)
- Pin base image versions (e.g., `python:3.12.3-slim`, not `python:3.12-slim`)

### Task 7.2: Network security
- Security Groups: only 22 (your IP), 80, 443 open
- K8s NetworkPolicies: restrict pod-to-pod communication (AI->HTTP allowed, AI->WS denied)
- **Concept**: Zero trust networking -- deny all, allow specific flows

### Task 7.3: Secrets management
- Audit all secrets, verify none in git history (`git log -S "SUPABASE"`)
- Never in Docker images (`docker history` to verify)
- Rotation procedure for all keys
- **Optional**: AWS Secrets Manager ($0.40/secret/month) for 3-4 secrets

### Task 7.4: Application-level security
- CORS: restrict to your domain only (not `*`)
- Rate limiting: 10/min auth, 60/min general (reuse Infinity middleware)
- JWT expiration: 1 hour tokens
- Security headers: CSP, X-Content-Type-Options, X-Frame-Options (reuse Infinity SecurityHeadersMiddleware)
- Request ID middleware for traceability

### Task 7.5: Security audit checklist
- [ ] No secrets in git history
- [ ] No secrets in Docker images
- [ ] SSH key has passphrase
- [ ] Minimal Security Group ports
- [ ] HTTPS enforced (HTTP -> HTTPS redirect)
- [ ] Non-root containers
- [ ] Dependencies up to date
- [ ] CORS domain-restricted
- [ ] Rate limiting active
- [ ] Logs don't contain secrets

---

## Summary

| Phase | Tasks | What You Learn |
|-------|-------|---------------|
| 1. Build the App | 8 | FastAPI microservices, WebSockets, AI integration |
| 2. Docker | 6 | Containers, images, Compose, networking |
| 3. AWS + Manual Deploy | 7 | EC2, Nginx, SSL, DNS |
| 4. CI/CD | 5 | GitHub Actions, automated deploy, rollback |
| 5. Kubernetes (k3s) | 6 | Orchestration, Deployments, Services, Ingress |
| 6. Monitoring | 4 | Prometheus, Grafana, alerting |
| 7. Security | 5 | Hardening every layer |
| **Total** | **41** | **Full-stack DevOps** |

## Cost: $0/month
- EC2 t3.micro: free tier (750h/month)
- Supabase: free tier
- Docker Hub: free
- GitHub Actions: free (2000 min/month)
- Let's Encrypt: free
- Domain: already owned
- **Warning**: Elastic IP costs $3.60/month if EC2 is stopped. Release it or keep instance running.

## Key Reference Files
- `metaverse/tests/index.test.js` -- Complete API specification (1039 lines)
- `Infinity/backend/app/main.py` -- FastAPI app skeleton to reuse
- `Infinity/backend/app/auth/dependencies.py` -- JWT auth pattern to adapt
- `Infinity/backend/app/config.py` -- Pydantic BaseSettings to reuse
- `Infinity/backend/app/middleware/rate_limiter.py` -- Production rate limiter to copy

## Verification
After each phase, verify:
- **Phase 1**: All pytest tests pass, all 3 services respond locally
- **Phase 2**: `docker compose up` starts everything, services communicate via Docker DNS
- **Phase 3**: App accessible at `https://yourdomain.com`, WebSocket works over `wss://`
- **Phase 4**: Push to main triggers build+deploy, rollback works
- **Phase 5**: `kubectl get pods` shows all running, Ingress routes correctly
- **Phase 6**: Grafana shows live metrics, alerts fire on simulated failure
- **Phase 7**: Security checklist all green
