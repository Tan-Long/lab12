# -*- coding: utf-8 -*-
"""
TravelBuddy Production API — Day 12 Lab Complete

Checklist:
  ✅ Config từ environment (12-factor)
  ✅ Structured JSON logging
  ✅ API Key authentication
  ✅ Rate limiting (sliding window)
  ✅ Cost guard (daily budget)
  ✅ Input validation (Pydantic)
  ✅ Health check + Readiness probe
  ✅ Graceful shutdown
  ✅ Security headers
  ✅ CORS
  ✅ LangGraph travel agent (Gemini)
  ✅ Multi-turn conversation (session_id)
"""
import time
import uuid
import signal
import logging
import json
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from app.config import settings
from app.auth import verify_api_key
from app.rate_limiter import check_rate_limit
from app.cost_guard import check_and_record_cost, get_daily_cost
import travel_agent

# ─────────────────────────────────────────────────────────
# Logging — JSON structured
# ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False
_request_count = 0
_error_count = 0

# ─────────────────────────────────────────────────────────
# Lifespan — init agent at startup
# ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }))
    if settings.gemini_api_key:
        travel_agent.init_agent(settings.gemini_api_key, settings.llm_model)
    else:
        logger.warning(json.dumps({"event": "no_gemini_key", "msg": "GEMINI_API_KEY not set"}))
    _is_ready = True
    logger.info(json.dumps({"event": "ready"}))

    yield

    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))

# ─────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count, _error_count
    start = time.time()
    _request_count += 1
    try:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if "server" in response.headers:
            del response.headers["server"]
        duration = round((time.time() - start) * 1000, 1)
        logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": duration,
        }))
        return response
    except Exception:
        _error_count += 1
        raise

# ─────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────
class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000,
                          description="Câu hỏi du lịch của bạn")
    session_id: str | None = Field(
        None,
        description="ID phiên hội thoại (để duy trì lịch sử). Bỏ trống để tạo phiên mới."
    )

class AskResponse(BaseModel):
    question: str
    answer: str
    session_id: str
    model: str
    timestamp: str

# ─────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "description": "TravelBuddy — Trợ lý du lịch Việt Nam",
        "endpoints": {
            "ask":     "POST /ask (requires X-API-Key)",
            "session": "DELETE /session/{id} (xóa lịch sử hội thoại)",
            "health":  "GET /health",
            "ready":   "GET /ready",
            "metrics": "GET /metrics (requires X-API-Key)",
            "docs":    "GET /docs" if settings.environment != "production" else "(disabled in production)",
        },
    }


@app.post("/ask", response_model=AskResponse, tags=["Travel Agent"])
async def ask_agent(
    body: AskRequest,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """
    Hỏi TravelBuddy về kế hoạch du lịch.

    Hỗ trợ hội thoại multi-turn — truyền `session_id` từ response trước để duy trì lịch sử.

    **Authentication:** Header `X-API-Key: <your-key>`
    """
    if not settings.gemini_api_key:
        raise HTTPException(503, "GEMINI_API_KEY not configured on server.")

    # Rate limit per API key
    check_rate_limit(_key[:8])

    # Estimate input tokens for cost guard
    input_tokens = len(body.question.split()) * 2
    check_and_record_cost(input_tokens, 0)

    session_id = body.session_id or str(uuid.uuid4())

    logger.info(json.dumps({
        "event": "agent_call",
        "q_len": len(body.question),
        "session_id": session_id[:8],
        "client": str(request.client.host) if request.client else "unknown",
    }))

    answer = travel_agent.ask_travel(body.question, session_id)

    output_tokens = len(answer.split()) * 2
    check_and_record_cost(0, output_tokens)

    return AskResponse(
        question=body.question,
        answer=answer,
        session_id=session_id,
        model=settings.llm_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.delete("/session/{session_id}", tags=["Travel Agent"])
def clear_session(
    session_id: str,
    _key: str = Depends(verify_api_key),
):
    """Xóa lịch sử hội thoại của một phiên."""
    travel_agent.clear_session(session_id)
    return {"deleted": session_id}


@app.get("/health", tags=["Operations"])
def health():
    """Liveness probe."""
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "llm": settings.llm_model,
        "gemini_configured": bool(settings.gemini_api_key),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["Operations"])
def ready():
    """Readiness probe."""
    if not _is_ready:
        raise HTTPException(503, "Not ready")
    return {"ready": True}


@app.get("/metrics", tags=["Operations"])
def metrics(_key: str = Depends(verify_api_key)):
    """Basic metrics (protected)."""
    daily_cost = get_daily_cost()
    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "error_count": _error_count,
        "daily_cost_usd": round(daily_cost, 6),
        "daily_budget_usd": settings.daily_budget_usd,
        "budget_used_pct": round(daily_cost / settings.daily_budget_usd * 100, 2),
        "model": settings.llm_model,
    }


# ─────────────────────────────────────────────────────────
# Graceful Shutdown
# ─────────────────────────────────────────────────────────
def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))

signal.signal(signal.SIGTERM, _handle_signal)


if __name__ == "__main__":
    logger.info(f"Starting {settings.app_name} on {settings.host}:{settings.port}")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
