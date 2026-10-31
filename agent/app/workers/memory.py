"""轻量记忆侧：从 input / trace_snapshot 提取错因等信号。"""

from __future__ import annotations

from typing import Any

from app.schemas.request import AgentRequest


def extract_error_tag(req: AgentRequest) -> str | None:
    raw = (req.input or {}).get("error_tag")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()

    tags = (req.input or {}).get("error_tags")
    if isinstance(tags, list) and tags:
        first = tags[0]
        if isinstance(first, str) and first.strip():
            return first.strip()

    snap = req.trace_snapshot or {}
    recent = snap.get("recent_attempts")
    if isinstance(recent, list):
        for item in reversed(recent):
            if not isinstance(item, dict):
                continue
            tag = item.get("error_tag")
            if isinstance(tag, str) and tag.strip():
                return tag.strip()
    return None


def primary_knowledge(req: AgentRequest) -> tuple[str, str]:
    if req.resource_refs:
        ref = req.resource_refs[0]
        return ref.id, (ref.label or ref.id)
    kid = (req.input or {}).get("knowledge_id")
    if isinstance(kid, str) and kid.strip():
        return kid.strip(), kid.strip()
    return "math.limit", "极限与连续"


def strategy_payload(error_tag: str, strategy: dict[str, Any]) -> dict[str, Any]:
    return {
        "error_tag": error_tag,
        "strategy_id": strategy.get("strategy_id"),
        "recommendation": strategy.get("recommendation"),
        "blackboard_type": strategy.get("blackboard_type"),
        "action": strategy.get("action"),
    }
