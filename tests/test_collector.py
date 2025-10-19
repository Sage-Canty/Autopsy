"""
tests/test_collector.py — unit tests for context building
"""

from datetime import datetime
from src.collector import build_context


def make_context(**kwargs):
    defaults = dict(
        log_group="/aws/ecs/test-service",
        start_time=datetime(2026, 4, 8, 2, 0, 0),
        end_time=datetime(2026, 4, 8, 3, 0, 0),
        alert="ECS TaskCount dropped below threshold",
        logs=[],
        deploys=[],
    )
    defaults.update(kwargs)
    return build_context(**defaults)


def test_build_context_duration():
    ctx = make_context()
    assert ctx["duration_minutes"] == 60


def test_build_context_no_logs():
    ctx = make_context()
    assert ctx["total_log_events"] == 0
    assert ctx["error_log_count"] == 0


def test_build_context_error_log_filtering():
    logs = [
        {"timestamp": "2026-04-08T02:01:00", "message": "Connection refused to db"},
        {"timestamp": "2026-04-08T02:02:00", "message": "Service started successfully"},
        {"timestamp": "2026-04-08T02:03:00", "message": "FATAL: out of memory"},
        {"timestamp": "2026-04-08T02:04:00", "message": "GET /health 200"},
    ]
    ctx = make_context(logs=logs)
    assert ctx["total_log_events"] == 4
    assert ctx["error_log_count"] == 2
    error_messages = [e["message"] for e in ctx["error_logs"]]
    assert any("refused" in m for m in error_messages)
    assert any("FATAL" in m for m in error_messages)


def test_build_context_log_cap():
    logs = [
        {"timestamp": f"2026-04-08T02:{i:02d}:00", "message": f"event {i}"}
        for i in range(300)
    ]
    ctx = make_context(logs=logs)
    assert len(ctx["all_logs"]) == 200


def test_build_context_error_log_cap():
    logs = [
        {"timestamp": f"2026-04-08T02:{i:02d}:00", "message": f"error event {i}"}
        for i in range(100)
    ]
    ctx = make_context(logs=logs)
    assert len(ctx["error_logs"]) == 50


def test_build_context_deploys():
    deploys = [
        {
            "time": "2026-04-08T01:30:00Z",
            "workflow": "Deploy to Production",
            "status": "success",
            "commit": "abc12345",
            "commit_message": "fix: update connection pool size",
            "author": "sage",
            "url": "https://github.com/org/repo/actions/runs/123",
        }
    ]
    ctx = make_context(deploys=deploys)
    assert len(ctx["deploys"]) == 1
    assert len(ctx["recent_deploys"]) == 1


def test_build_context_recent_deploys_filters_cancelled():
    deploys = [
        {"time": "2026-04-08T01:00:00Z", "workflow": "Deploy", "status": "cancelled",
         "commit": "aaa", "commit_message": "test", "author": "sage", "url": ""},
        {"time": "2026-04-08T01:30:00Z", "workflow": "Deploy", "status": "failure",
         "commit": "bbb", "commit_message": "fix", "author": "sage", "url": ""},
    ]
    ctx = make_context(deploys=deploys)
    assert len(ctx["recent_deploys"]) == 1
    assert ctx["recent_deploys"][0]["status"] == "failure"
