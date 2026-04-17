# Day 12 Lab - Mission Answers

**Student Name:** Nguyễn Hữu Tân Long  
**Student ID:** 2A202600168  
**Date:** 17/4/2026

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found in `develop/app.py`

1. **API key hardcoded trong code** (dòng 17-18) — `OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"` và `DATABASE_URL = "postgresql://admin:password123@localhost:5432/mydb"`. Push lên GitHub → key bị lộ ngay lập tức.

2. **Config cứng, không linh hoạt** (dòng 21-22) — `DEBUG = True` và `MAX_TOKENS = 500` hardcode. Không thể thay đổi giữa dev/staging/production mà không sửa code.

3. **Dùng `print()` thay vì logging, và log ra secret** (dòng 33-34) — `print(f"[DEBUG] Using key: {OPENAI_API_KEY}")` ghi secret vào stdout. Log aggregator sẽ thu thập secret này.

4. **Không có health check endpoint** (comment dòng 42) — Platform (Railway, Render, K8s) không biết container có còn sống không, không thể tự restart khi crash.

5. **`host="localhost"`, port cứng, `reload=True`** (dòng 51-53) — `localhost` chỉ nhận kết nối nội bộ, container sẽ không nhận traffic từ bên ngoài. `reload=True` tốn CPU và không an toàn trên production.

### Exercise 1.3: Comparison table

| Feature | Develop | Production | Tại sao quan trọng? |
|---------|---------|------------|---------------------|
| Config | Hardcode trong code | Đọc từ environment variables qua `os.getenv()` | Bảo mật secrets, dễ thay đổi giữa environments mà không sửa code |
| Health check | Không có | `/health` (liveness) + `/ready` (readiness) | Platform biết khi nào restart container; load balancer biết khi nào route traffic |
| Logging | `print()` + log secrets | JSON structured, không log secrets | Dễ parse bởi Datadog/Loki; secrets không xuất hiện trong log |
| Shutdown | Đột ngột (process kill) | Graceful — SIGTERM handler + lifespan context manager | Requests đang xử lý được hoàn thành trước khi container tắt |
| Host binding | `localhost` (chỉ nội bộ) | `0.0.0.0` (nhận từ bên ngoài container) | Bắt buộc khi chạy trong Docker/cloud |

---

## Part 2: Docker Containerization

### Exercise 2.1: Dockerfile questions (`develop/`)

1. **Base image:** `python:3.11` — full Python distribution (~1GB)
2. **Working directory:** `/app`
3. **Tại sao COPY requirements.txt trước?** — Docker build theo từng layer. Nếu `requirements.txt` không đổi, layer install dependencies được cache lại. Chỉ khi thay đổi requirements mới reinstall, giúp build nhanh hơn nhiều lần khi chỉ sửa code.
4. **CMD vs ENTRYPOINT:** `CMD` là lệnh mặc định, có thể override khi `docker run`. `ENTRYPOINT` là lệnh cố định, không override được (chỉ append thêm args). Dùng `CMD` cho flexibility.

### Exercise 2.3: Multi-stage build — image size comparison

| Image | Size |
|-------|------|
| `agent-develop` (single-stage, `python:3.11`) | **1.66 GB** |
| `agent-production` (multi-stage, `python:3.11-slim`) | **236 MB** |
| **Giảm** | **~86% (~7x nhỏ hơn)** |

**Tại sao multi-stage nhỏ hơn?**
- Stage 1 (builder): dùng `python:3.11-slim` + cài `gcc`, `libpq-dev`, install packages với `--user`
- Stage 2 (runtime): chỉ copy `/root/.local` (packages đã compile) sang image mới sạch — không có build tools, không có pip cache, không có source của compiler

### Exercise 2.4: Docker Compose stack architecture

```
Internet
   │
[Nginx :80] ← reverse proxy + rate limiting (10 req/s per IP)
   │  round-robin
   ├── [Agent :8000] ← FastAPI + health check
   ├── [Agent :8000] ← (scale = 3)
   └── [Agent :8000]
           │
        [Redis :6379] ← session cache, rate limiting state
        [Qdrant :6333] ← vector database (optional)
```

Services communicate qua internal Docker network `agent_net` — không expose port agent trực tiếp ra ngoài, chỉ qua Nginx.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

- **Public URL:** https://lab12-production-9667.up.railway.app
- **Health check:** `curl https://lab12-production-9667.up.railway.app/health`
  ```json
  {"status":"ok","uptime_seconds":155.0,"platform":"Railway","timestamp":"..."}
  ```
- **API test:**
  ```bash
  curl -X POST https://lab12-production-9667.up.railway.app/ask \
    -H "X-API-Key: my-secret-key-2026" \
    -H "Content-Type: application/json" \
    -d '{"question": "What is Docker?"}'
  ```

**Các bước thực hiện:**
1. `cd 03-cloud-deployment/railway`
2. `railway login` → xác thực qua browser
3. `railway init` → tạo project mới
4. `railway variables set AGENT_API_KEY=my-secret-key-2026`
5. `railway up` → deploy (Nixpacks auto-detect Python)
6. `railway domain` → nhận URL public

### Exercise 3.2: So sánh `render.yaml` vs `railway.toml`

| | `railway.toml` | `render.yaml` |
|-|----------------|---------------|
| Format | TOML | YAML |
| Build | Nixpacks (auto-detect) hoặc Dockerfile | `buildCommand` tường minh |
| Start | `startCommand` | `startCommand` |
| Health check | `healthcheckPath` | `healthCheckPath` |
| Env vars | Set qua CLI/Dashboard | Khai báo trong file + `generateValue: true` |
| Redis | Separate service | `type: redis` cùng file |
| IaC | Partial | Full (toàn bộ stack trong 1 file) |

---

## Part 4: API Security

### Exercise 4.1: API Key authentication — test results

```bash
# Không có key → 401
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"hello"}'
# Response: 401 {"detail":"Missing API key..."}

# Sai key → 403
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: wrong-key" \
  -H "Content-Type: application/json" \
  -d '{"question":"hello"}'
# Response: 403 {"detail":"Invalid API key."}

# Đúng key → 200
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: demo-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"question":"hello"}'
# Response: 200 {"question":"hello","answer":"..."}
```

### Exercise 4.2: JWT authentication flow

```
1. POST /auth/token  {username, password}
   → Server verify credentials
   → Tạo JWT: {sub, role, iat, exp} signed bằng SECRET_KEY
   → Trả về {"access_token": "eyJ...", "expires_in_minutes": 60}

2. POST /ask  Authorization: Bearer eyJ...
   → Server decode JWT với SECRET_KEY
   → Extract {username, role} từ payload
   → Xử lý request với user context

Demo credentials:
  student / demo123  → role: user  (10 req/min)
  teacher / teach456 → role: admin (100 req/min)
```

**Test:**
```
Step 1 - Get token: OK (200)
Step 2 - Ask with token: 200
Step 3 - Ask no token: 401
Step 4 - Ask bad token: 403
Step 5 - Health: 200, status=ok
```

### Exercise 4.3: Rate limiting

**Algorithm:** Sliding Window Counter dùng `collections.deque`

**Cách hoạt động:**
- Mỗi user có 1 deque chứa timestamps của các requests
- Mỗi request: loại bỏ timestamps cũ hơn 60 giây, đếm còn lại
- Nếu `len(window) >= max_requests` → raise 429
- Limit: user = 10 req/min, admin = 100 req/min

**Bypass cho admin:** Role `admin` dùng `rate_limiter_admin` (100 req/min) thay vì `rate_limiter_user` (10 req/min).

Response header khi bị limit:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
Retry-After: <seconds>
```

### Exercise 4.4: Cost guard implementation

`cost_guard.py` implement theo approach:
- **Per-user daily budget:** $1.00/ngày — track `input_tokens` + `output_tokens` trong `UsageRecord`
- **Global daily budget:** $10.00/ngày — tổng tất cả users
- **Giá:** input $0.15/1M tokens, output $0.60/1M tokens (GPT-4o-mini pricing)
- **Reset:** tự động reset khi sang ngày mới (check `time.strftime("%Y-%m-%d")`)
- **HTTP codes:** 402 (user budget exceeded), 503 (global budget exceeded)
- **Warning:** log cảnh báo khi user dùng ≥ 80% budget

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks implementation

```python
@app.get("/health")
def health():
    """Liveness probe — "Agent có còn sống không?"
    Platform gọi định kỳ, restart nếu fail."""
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "checks": {"memory": {"status": "ok", "used_percent": mem.percent}}
    }

@app.get("/ready")
def ready():
    """Readiness probe — "Sẵn sàng nhận traffic chưa?"
    Load balancer không route vào nếu trả về 503."""
    if not _is_ready:
        raise HTTPException(503, "Agent not ready")
    return {"ready": True, "in_flight_requests": _in_flight_requests}
```

Test:
```
Health: ok | checks: ['memory']
Ready: True | in_flight: 1
```

### Exercise 5.2: Graceful shutdown

```python
def handle_sigterm(signum, frame):
    logger.info(f"Received signal {signum} — uvicorn will handle graceful shutdown")

signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)
```

Lifespan shutdown đợi in-flight requests hoàn thành (tối đa 30 giây):
```python
while _in_flight_requests > 0 and elapsed < timeout:
    time.sleep(1)
    elapsed += 1
```

### Exercise 5.3: Stateless design

**Anti-pattern (không làm):**
```python
conversation_history = {}  # mỗi instance có memory riêng → mất data khi scale
```

**Correct (stateless với Redis):**
```python
def save_session(session_id, data):
    _redis.setex(f"session:{session_id}", 3600, json.dumps(data))

def load_session(session_id):
    data = _redis.get(f"session:{session_id}")
    return json.loads(data) if data else {}
```

Bất kỳ instance nào cũng đọc/ghi được session của user qua Redis.

### Exercise 5.4 & 5.5: Load balancing + Stateless test

```
docker compose up --scale agent=3
python test_stateless.py
```

**Kết quả:**
```
Session ID: ac3aaa89-ef21-405c-8fba-534a52a28689

Request 1: [instance-11af7d]  Q: What is Docker?
Request 2: [instance-01002c]  Q: Why do we need containers?
Request 3: [instance-3ba2aa]  Q: What is Kubernetes?
Request 4: [instance-11af7d]  Q: How does load balancing work?
Request 5: [instance-01002c]  Q: What is Redis used for?

Instances used: {'instance-01002c', 'instance-11af7d', 'instance-3ba2aa'}
✅ All requests served despite different instances!

Total messages: 10
✅ Session history preserved across all instances via Redis!
```

**Kết luận:** 5 requests đi qua 3 instance khác nhau (Nginx round-robin), nhưng conversation history vẫn đầy đủ vì state lưu trong Redis chứ không trong memory của instance.
