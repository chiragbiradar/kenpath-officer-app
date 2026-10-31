from datetime import datetime, timedelta, timezone
import pytest
from app.priority import deadline_status, priority_score
from app.rules import RuleResult


def make_result(status):
    return RuleResult("R1", status, "", "")


now = datetime.now(timezone.utc)


def test_overdue():
    dl = now - timedelta(days=2)
    assert deadline_status(dl) == "overdue"
    score = priority_score(dl, [])
    assert score >= 1000


def test_due_soon():
    dl = now + timedelta(hours=12)
    assert deadline_status(dl) == "due_soon"
    score = priority_score(dl, [])
    assert 500 <= score < 1000


def test_on_track():
    dl = now + timedelta(days=5)
    assert deadline_status(dl) == "on_track"
    score = priority_score(dl, [])
    assert score < 500


def test_fail_adds_score():
    dl = now + timedelta(days=5)
    base = priority_score(dl, [])
    with_fail = priority_score(dl, [make_result("fail")])
    assert with_fail == base + 20


def test_review_adds_score():
    dl = now + timedelta(days=5)
    base = priority_score(dl, [])
    with_review = priority_score(dl, [make_result("review")])
    assert with_review == base + 10
