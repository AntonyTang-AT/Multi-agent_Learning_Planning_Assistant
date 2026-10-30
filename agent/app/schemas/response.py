"""Agent invoke 响应 schema（对齐 docs/agent-api.md · 技术路线 §4）。"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ResponseStatus(str, Enum):
    ok = "ok"
    conflict = "conflict"
    doubt = "doubt"
    failed = "failed"
    abstain = "abstain"
    need_user = "need_user"


class BlackboardEntry(BaseModel):
    entry_id: str
    type: str
    summary: str
    severity: str = "medium"
    evidence_refs: list[str] = Field(default_factory=list)
    status: str = "open"


class UserOption(BaseModel):
    id: str
    label: str


class ResponseMeta(BaseModel):
    agent_version: str = "0.1.0"
    latency_ms: int = 0


class AgentResponse(BaseModel):
    request_id: str
    task_id: str
    status: ResponseStatus
    message: str = ""
    output: dict[str, Any] = Field(default_factory=dict)
    blackboard_entries: list[BlackboardEntry] = Field(default_factory=list)
    user_options: list[UserOption] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
