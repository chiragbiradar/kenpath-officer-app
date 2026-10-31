from datetime import datetime, timezone
from typing import Literal

from app.rules import RuleResult


def _ensure_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def deadline_status(deadline_at: datetime) -> Literal["overdue", "due_soon", "on_track"]:
    days_left = (_ensure_utc(deadline_at) - datetime.now(timezone.utc)).days
    if days_left < 0:
        return "overdue"
    if days_left <= 1:
        return "due_soon"
    return "on_track"


def priority_score(deadline_at: datetime, rule_results: list[RuleResult]) -> int:
    days_left = (_ensure_utc(deadline_at) - datetime.now(timezone.utc)).days
    if days_left < 0:
        score = 1000 + abs(days_left)
    elif days_left <= 1:
        score = 500 + (1 - days_left)
    else:
        score = max(0, 100 - days_left)

    fails = sum(1 for r in rule_results if r.status == "fail")
    reviews = sum(1 for r in rule_results if r.status == "review")
    score += 20 * fails + 10 * reviews
    return score
