# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an educational Python/FastAPI project for Day 12 of AICB-P1 at VinUniversity 2026. It teaches production-ready AI agent deployment through 6 progressive sections, each comparing `develop/` (anti-patterns) vs `production/` (best practices).

## Running Examples Locally

Each section has its own `requirements.txt`. Install per section:

```bash
cd <section>/production
pip install -r requirements.txt
python app.py
# or with uvicorn: uvicorn app:app --host 0.0.0.0 --port 8000
```

Docker-based sections:

```bash
# Single container
docker build -t agent . && docker run -p 8000:8000 agent

# Multi-service (with Redis/Nginx)
docker compose up

# Scale horizontally
docker compose up --scale agent=3
```

## Testing Endpoints

```bash
# Health/readiness probes
curl http://localhost:8000/health
curl http://localhost:8000/ready

# Unauthenticated ask (expect 401 in production sections)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'

# Authenticated ask (Part 4+)
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'

# Rate limit test
for i in {1..25}; do curl -s -H "X-API-Key: key" -X POST ... ; done
```

## Production Readiness Validation (Part 6)

```bash
cd 06-lab-complete
python check_production_ready.py
```

## Deployment

```bash
# Railway
railway login && railway init
railway variables set AGENT_API_KEY=your-key
railway up && railway domain

# Render: connect repo via dashboard, render.yaml is auto-detected

# Docker debug
docker exec -it <container> /bin/sh
docker compose logs -f agent
```

## Architecture

### Section Structure

| Section | Focus |
|---------|-------|
| `01-localhost-vs-production/` | 12-factor config, env vars vs hardcoded secrets |
| `02-docker/` | Single-stage vs multi-stage Dockerfile, Docker Compose |
| `03-cloud-deployment/` | Railway (`railway.toml`), Render (`render.yaml`), GCP Cloud Run |
| `04-api-gateway/` | API key → JWT auth, rate limiting (`rate_limiter.py`), cost guard (`cost_guard.py`) |
| `05-scaling-reliability/` | Stateless design, Redis-backed state, Nginx load balancing |
| `06-lab-complete/` | All concepts combined into one production-ready agent |

### Mock LLM

`utils/mock_llm.py` is a shared mock that requires no API key. It provides `ask(question)` and `ask_stream(question)`. All sections use this so the code runs offline.

### Standard Request Pipeline (Part 4+)

```
Request → CORS middleware → request logging → API key/JWT validation
        → rate limiter (429) → input validation (Pydantic) 
        → cost guard (503) → mock_llm.ask() → JSON response
```

### Key Files Per Section

- `app.py` or `app/main.py` — FastAPI app with `/`, `/ask`, `/health`, `/ready`, `/metrics`
- `config.py` — 12-factor settings loaded from environment variables
- `Dockerfile` — Multi-stage: builder (`python:3.11`) → runtime (`python:3.11-slim`)
- `docker-compose.yml` — Agent + Redis services with healthchecks and restart policies
- `.env.example` — Template for required environment variables (never commit `.env`)

### Environment Variables

Key vars (see `.env.example` in each production section):

```
HOST, PORT, ENVIRONMENT, DEBUG
AGENT_API_KEY         # X-API-Key header for /ask
JWT_SECRET            # JWT signing (Part 4+)
RATE_LIMIT_PER_MINUTE # Default: 20
DAILY_BUDGET_USD      # Default: 5.0
REDIS_URL             # redis://localhost:6379/0 (Part 5+)
OPENAI_API_KEY        # Optional — mock LLM used if empty
```

### Security Patterns (Part 4+)

- Authentication: `APIKeyHeader(name="X-API-Key")` or JWT Bearer
- Rate limiting: token bucket via `collections.deque` (in-memory) or Redis (scaled)
- Cost guard: daily token budget tracker returning 503 when exhausted
- Container: non-root user `agent`, `HEALTHCHECK` directive, no secrets baked into image
