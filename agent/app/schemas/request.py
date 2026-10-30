"""Agent invoke 请求 schema（对齐 docs/agent-api.md · 技术路线 §4）。"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Intent(str, Enum):
    """MVP intent + A1 调试用 echo。"""

    create_plan = "create_plan"
    arbitrate = "arbitrate"
    generate_question = "generate_question"
    verify_answer = "verify_answer"
    record_trace = "record_trace"
    challenge = "challenge"
    metacognitive_feedback = "metacognitive_feedback"
    proactive_intervention = "proactive_intervention"
    echo = "echo"  # A1 调试回声，后续可删


class Scenario(str, Enum):
    final_review = "final_review"
    catch_up = "catch_up"


class Constraints(BaseModel):
    hard: list[str] = Field(default_factory=list)
    soft: list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    user_id: str = "anonymous"
    constraints: Constraints = Field(default_factory=Constraints)


class ResourceRef(BaseModel):
    type: str
    id: str
    label: str | None = None


class DemoFlags(BaseModel):
    force_conflict: bool = False
    force_verify_fail: bool = False
    time_jump_days: int = 0


class AgentRequest(BaseModel):
    request_id: str
    task_id: str
    scenario: Scenario = Scenario.final_review
    intent: str  # 用 str 以便未知 intent 在编排层返回明确错误，而非直接 422
    user_profile: UserProfile = Field(default_factory=UserProfile)
    input: dict[str, Any] = Field(default_factory=dict)
    resource_refs: list[ResourceRef] = Field(default_factory=list)
    resource_payload: dict[str, Any] = Field(default_factory=dict)
    trace_snapshot: dict[str, Any] = Field(default_factory=dict)
    demo: DemoFlags = Field(default_factory=DemoFlags)
