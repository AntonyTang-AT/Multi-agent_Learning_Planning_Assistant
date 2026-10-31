"""A4 验收：错因策略差异 + 黑板类型。"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.rules.error_strategy import list_error_tags

client = TestClient(app)
EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_at_least_four_error_tags() -> None:
    assert len(list_error_tags()) >= 4


def test_limit_misuse_inserts_concept_review_and_challenge_bb() -> None:
    example = json.loads(
        (EXAMPLES / "create_plan_error_limit_misuse.json").read_text(encoding="utf-8")
    )
    r = client.post("/agent/v1/invoke", json=example["request"])
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    strategy = body["output"]["error_strategy"]
    assert strategy["error_tag"] == "limit_misuse"
    assert strategy["action"] == "回顾概念"
    tasks = body["output"]["plan"]["tasks"]
    assert tasks[0]["remediation"] is True
    assert tasks[0]["action"] == "回顾概念"
    types = {e["type"] for e in body["blackboard_entries"]}
    assert "challenge" in types


def test_symbol_error_differs_from_limit_misuse() -> None:
    ex_a = json.loads(
        (EXAMPLES / "create_plan_error_limit_misuse.json").read_text(encoding="utf-8")
    )
    ex_b = json.loads(
        (EXAMPLES / "create_plan_error_symbol_error.json").read_text(encoding="utf-8")
    )
    a = client.post("/agent/v1/invoke", json=ex_a["request"]).json()
    b = client.post("/agent/v1/invoke", json=ex_b["request"]).json()

    assert a["output"]["error_strategy"]["strategy_id"] != b["output"]["error_strategy"]["strategy_id"]
    assert a["output"]["error_strategy"]["action"] != b["output"]["error_strategy"]["action"]
    assert a["output"]["plan"]["tasks"][0]["object"] != b["output"]["plan"]["tasks"][0]["object"]

    types_b = {e["type"] for e in b["blackboard_entries"]}
    assert "intervention" in types_b


def test_undefined_assumption_and_conceptual_gap_cover_bb_types() -> None:
    base = {
        "task_id": "t",
        "scenario": "final_review",
        "intent": "create_plan",
        "user_profile": {"constraints": {"hard": ["daily_minutes<=120"]}},
        "resource_refs": [{"type": "knowledge", "id": "math.limit", "label": "极限与连续"}],
        "demo": {"force_conflict": False},
        "input": {"days_left": 4},
    }
    seen: set[str] = set()
    for tag in ("undefined_assumption", "conceptual_gap", "limit_misuse", "symbol_error"):
        payload = {
            **base,
            "request_id": f"req_{tag}",
            "input": {**base["input"], "error_tag": tag},
        }
        body = client.post("/agent/v1/invoke", json=payload).json()
        assert body["status"] == "ok"
        seen |= {e["type"] for e in body["blackboard_entries"]}
    assert "challenge" in seen
    assert "intervention" in seen
