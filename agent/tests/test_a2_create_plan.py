"""A2 验收：create_plan 审计冲突 + arbitrate。"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_create_plan_ok() -> None:
    payload = {
        "request_id": "req_ok",
        "task_id": "task_ok",
        "scenario": "final_review",
        "intent": "create_plan",
        "user_profile": {
            "user_id": "u1",
            "constraints": {"hard": ["daily_minutes<=120", "subject=math"], "soft": []},
        },
        "input": {"goal": "期末过线", "days_left": 7},
        "resource_refs": [
            {"type": "knowledge", "id": "math.limit", "label": "极限与连续"},
            {"type": "knowledge", "id": "math.derivative", "label": "导数与微分"},
        ],
        "demo": {"force_conflict": False},
    }
    r = client.post("/agent/v1/invoke", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["output"]["plan"]["tasks"]
    assert all(t.get("completion_criteria") for t in body["output"]["plan"]["tasks"])


def test_create_plan_force_conflict_matches_example_shape() -> None:
    example = json.loads((EXAMPLES / "create_plan_final_review.json").read_text(encoding="utf-8"))
    r = client.post("/agent/v1/invoke", json=example["request"])
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "conflict"
    assert "第3天" in body["message"] and "45" in body["message"]
    assert len(body["user_options"]) == 3
    ids = {o["id"] for o in body["user_options"]}
    assert ids == {"extend_time", "reduce_depth", "adjust_goal"}
    assert body["blackboard_entries"]
    assert body["blackboard_entries"][0]["type"] == "conflict"
    assert body["requires_approval"] is True
    assert body["output"]["plan"]["tasks"]


def test_arbitrate_extend_time() -> None:
    example = json.loads((EXAMPLES / "arbitrate_extend_time.json").read_text(encoding="utf-8"))
    r = client.post("/agent/v1/invoke", json=example["request"])
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["output"]["plan"]["arbitration"]["option_id"] == "extend_time"
    assert body["output"]["plan"]["daily_minutes_budget"] >= 60


def test_arbitrate_reduce_depth() -> None:
    plan = {
        "goal": "期末过线",
        "daily_minutes_budget": 45,
        "tasks": [
            {
                "day": 1,
                "action": "复习",
                "object": "极限",
                "minutes": 50,
                "completion_criteria": "完成3道基础填空",
                "load": "high",
                "knowledge_ids": ["math.limit"],
            }
        ],
    }
    payload = {
        "request_id": "req_rd",
        "task_id": "task_rd",
        "intent": "arbitrate",
        "user_profile": {"constraints": {"hard": ["daily_minutes<=45"]}},
        "input": {"option_id": "reduce_depth", "plan": plan},
    }
    r = client.post("/agent/v1/invoke", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    task = body["output"]["plan"]["tasks"][0]
    assert task["minutes"] <= 30
    assert task["load"] == "low"
