"""A3 验收：出题/校验 + 弃答降级。"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_verify_answer_ok() -> None:
    example = json.loads((EXAMPLES / "verify_answer_ok.json").read_text(encoding="utf-8"))
    r = client.post("/agent/v1/invoke", json=example["request"])
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["output"]["verdict"] == "passed"
    assert body["output"]["audit_trail"]


def test_verify_answer_force_fail_abstain() -> None:
    example = json.loads((EXAMPLES / "verify_answer_force_fail.json").read_text(encoding="utf-8"))
    r = client.post("/agent/v1/invoke", json=example["request"])
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "abstain"
    assert body["output"]["verdict"] == "failed"
    assert body["output"].get("hint_mode") is True
    assert "audit_trail" in body["output"]


def test_verify_wrong_answer_abstain() -> None:
    payload = {
        "request_id": "req_wrong",
        "task_id": "task_wrong",
        "intent": "verify_answer",
        "input": {
            "answer": "0",
            "verify_hint": {"expr": "limit(sin(x)/x, x, 0)", "expected": "1"},
        },
        "demo": {"force_verify_fail": False},
    }
    r = client.post("/agent/v1/invoke", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "abstain"
    assert body["output"]["verdict"] == "failed"


def test_generate_question_ok_from_payload() -> None:
    example = json.loads((EXAMPLES / "generate_question_ok.json").read_text(encoding="utf-8"))
    r = client.post("/agent/v1/invoke", json=example["request"])
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["output"]["question"]["stem"]
    assert body["output"]["verdict"] == "passed"


def test_generate_question_force_abstain() -> None:
    example = json.loads(
        (EXAMPLES / "generate_question_force_abstain.json").read_text(encoding="utf-8")
    )
    r = client.post("/agent/v1/invoke", json=example["request"])
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "abstain"
    assert body["output"]["question"] is None
    assert body["output"].get("hint_mode") is True
