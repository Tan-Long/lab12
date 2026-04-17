"""
In-Memory Rate Limiter — Sliding Window

Giới hạn số request mỗi key trong 60 giây.
Limit được set qua RATE_LIMIT_PER_MINUTE environment variable.

Lưu ý: in-memory → reset khi restart. Dùng Redis cho production multi-instance.
"""
import time
from collections import defaultdict, deque
from fastapi import HTTPException

from app.config import settings

_rate_windows: dict[str, deque] = defaultdict(deque)


def check_rate_limit(key: str) -> None:
    """
    Kiểm tra và ghi nhận request cho key.
    Raise 429 nếu vượt rate limit.
    """
    now = time.time()
    window = _rate_windows[key]

    # Loại bỏ timestamps ngoài sliding window 60 giây
    while window and window[0] < now - 60:
        window.popleft()

    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
            headers={"Retry-After": "60"},
        )

    window.append(now)
