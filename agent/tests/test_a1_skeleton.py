"""A1 验收：health + echo 回声 + 未知 intent 明确错误。"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "up"
    assert "version" in body


def test_echo_invoke() -> None:
    payload = {
        "request_id": "req_test_echo",
        "task_id": "task_test_echo",
        "scenario": "final_review",
        "intent": "echo",
        "input": {"hello": "world"},
        "demo": {"force_conflict": False},
    }
    r = client.post("/agent/v1/invoke", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["request_id"] == "req_test_echo"
    assert body["output"]["echo"] == {"hello": "world"}
    assert "meta" in body and "agent_version" in body["meta"]


def test_unknown_intent() -> None:
    payload = {
        "request_id": "req_bad",
        "task_id": "task_bad",
        "intent": "not_a_real_intent",
        "input": {},
    }
    r = client.post("/agent/v1/invoke", json=payload)
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert detail["code"] == "unknown_intent"
    assert "supported_intents" in detail


def test_pending_intent_placeholder() -> None:
    payload = {
        "request_id": "req_pending",
        "task_id": "task_pending",
        "intent": "record_trace",
        "input": {},
    }
    r = client.post("/agent/v1/invoke", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "failed"
    assert "尚未实现" in body["message"]
