"""A5 验收：三必演脚本 + Evaluator 增强。"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.demos.run_three_must import run
from app.main import app

client = TestClient(app)
EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_three_must_script() -> None:
    assert run(with_enhancements=False) == 0


def test_three_must_with_enhancements() -> None:
    assert run(with_enhancements=True) == 0


def test_challenge_missing_assumption() -> None:
    example = json.loads(
        (EXAMPLES / "challenge_missing_assumption.json").read_text(encoding="utf-8")
    )
    r = client.post("/agent/v1/invoke", json=example["request"])
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "need_user"
    assert body["output"]["card"]["type"] == "structured_challenge"
    assert any(e["type"] == "challenge" for e in body["blackboard_entries"])


def test_metacognitive_card() -> None:
    example = json.loads(
        (EXAMPLES / "metacognitive_feedback.json").read_text(encoding="utf-8")
    )
    r = client.post("/agent/v1/invoke", json=example["request"])
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["output"]["card"]["type"] == "metacognitive"


def test_proactive_intervention_time_jump() -> None:
    example = json.loads(
        (EXAMPLES / "proactive_intervention_time_jump.json").read_text(encoding="utf-8")
    )
    r = client.post("/agent/v1/invoke", json=example["request"])
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "need_user"
    assert body["output"]["triggered"] is True
    assert any(e["type"] == "intervention" for e in body["blackboard_entries"])
