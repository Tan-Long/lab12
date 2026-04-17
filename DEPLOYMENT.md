# Deployment Information

## Public URL

**https://lab12-production-9667.up.railway.app**

## Platform

**Railway** — deployed via Railway CLI with Nixpacks (auto-detect Python)

## Architecture

```
Client → Railway (Nixpacks) → uvicorn → FastAPI app
                                           ├── /health    (liveness probe)
                                           ├── /ready     (readiness probe)
                                           ├── /ask       (protected, X-API-Key)
                                           └── /          (public info)
```

## Environment Variables Set on Railway

| Variable | Description |
|----------|-------------|
| `PORT` | Injected automatically by Railway |
| `AGENT_API_KEY` | API key for /ask endpoint |
| `ENVIRONMENT` | `production` |

## Test Commands

### 1. Health Check
```bash
curl https://lab12-production-9667.up.railway.app/health
```
Expected:
```json
{"status":"ok","uptime_seconds":155.0,"platform":"Railway","timestamp":"..."}
```

### 2. Root Info (public)
```bash
curl https://lab12-production-9667.up.railway.app/
```

### 3. Authentication required — expect 401
```bash
curl -X POST https://lab12-production-9667.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

### 4. API Test with authentication — expect 200
```bash
curl -X POST https://lab12-production-9667.up.railway.app/ask \
  -H "X-API-Key: my-secret-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```
Expected:
```json
{
  "question": "What is Docker?",
  "answer": "Container là cách đóng gói app để chạy ở mọi nơi...",
  "platform": "Railway"
}
```

### 5. Rate limit test — expect 429 after limit
```bash
for i in {1..15}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST https://lab12-production-9667.up.railway.app/ask \
    -H "X-API-Key: my-secret-key-2026" \
    -H "Content-Type: application/json" \
    -d '{"question": "test"}';
done
```

## Local Setup

```bash
# Clone repo
git clone <your-repo-url>
cd day12_ha-tang-cloud_va_deployment

# Run Part 6 locally
cd 06-lab-complete
cp .env.example .env.local
# Edit .env.local: set AGENT_API_KEY

docker compose up
curl http://localhost:8000/health
```

## Production Readiness Check

```bash
cd 06-lab-complete
PYTHONUTF8=1 python check_production_ready.py
# Result: 20/20 checks passed (100%) — PRODUCTION READY!
```
