"""
Cost Guard — Daily Budget Protection

Bảo vệ khỏi bill bất ngờ từ LLM API.
Tính cost dựa trên token usage, block khi vượt DAILY_BUDGET_USD.

Pricing (GPT-4o-mini):
  Input:  $0.15 / 1M tokens
  Output: $0.60 / 1M tokens
"""
import time
from fastapi import HTTPException

from app.config import settings

_daily_cost: float = 0.0
_cost_reset_day: str = time.strftime("%Y-%m-%d")

PRICE_INPUT_PER_1K = 0.00015   # $0.15 / 1M tokens
PRICE_OUTPUT_PER_1K = 0.0006   # $0.60 / 1M tokens


def check_and_record_cost(input_tokens: int, output_tokens: int) -> None:
    """
    Kiểm tra budget và ghi nhận cost.
    Raise 503 nếu vượt daily budget.
    Auto-reset vào ngày mới.
    """
    global _daily_cost, _cost_reset_day

    today = time.strftime("%Y-%m-%d")
    if today != _cost_reset_day:
        _daily_cost = 0.0
        _cost_reset_day = today

    if _daily_cost >= settings.daily_budget_usd:
        raise HTTPException(
            status_code=503,
            detail=f"Daily budget exhausted (${settings.daily_budget_usd}). Try again tomorrow.",
        )

    cost = (input_tokens / 1000) * PRICE_INPUT_PER_1K + \
           (output_tokens / 1000) * PRICE_OUTPUT_PER_1K
    _daily_cost += cost


def get_daily_cost() -> float:
    return round(_daily_cost, 6)
