"""
Agent GCP Cloud Run-ready.
Cloud Run inject PORT env var tự động.
Optimized cho serverless: stateless, fast startup, graceful shutdown.
"""
import os
import signal
import time
import logging
import json
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from utils.mock_llm import ask

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
is_ready = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global is_ready
    logger.info(json.dumps({"event": "startup", "platform": "Cloud Run"}))
    is_ready = True
    yield
    is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))


app = FastAPI(title="Agent on Cloud Run", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "AI Agent running on GCP Cloud Run!",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "docs": "/docs",
    }


@app.post("/ask")
async def ask_agent(request: Request):
    body = await request.json()
    question = body.get("question", "")
    if not question:
        raise HTTPException(422, "question required")
    logger.info(json.dumps({"event": "request", "q_len": len(question)}))
    return {
        "question": question,
        "answer": ask(question),
        "platform": "Cloud Run",
    }


@app.get("/health")
def health():
    """Liveness probe — Cloud Run / Kubernetes."""
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready")
def ready():
    """Readiness probe — dùng trong service.yaml startupProbe."""
    if not is_ready:
        raise HTTPException(503, "not ready")
    return {"ready": True}


def handle_sigterm(*args):
    """Cloud Run gửi SIGTERM 10 giây trước khi force kill."""
    logger.info("Received SIGTERM — graceful shutdown")


signal.signal(signal.SIGTERM, handle_sigterm)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
