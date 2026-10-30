"""主 Agent：按 intent 路由到 Worker（A1：仅 echo + 未实现占位）。"""

from __future__ import annotations

import time
from typing import Callable

from app.config import get_settings
from app.schemas.request import AgentRequest, Intent
from app.schemas.response import AgentResponse, ResponseMeta, ResponseStatus
from app.workers import echo as echo_worker

Handler = Callable[[AgentRequest], AgentResponse]

# A1 已实现
_IMPLEMENTED: dict[str, Handler] = {
    Intent.echo.value: echo_worker.handle,
}

# MVP 合同中的 intent：A1 先占位，后续 A2+ 替换
_MVP_PENDING = {
    Intent.create_plan.value,
    Intent.arbitrate.value,
    Intent.generate_question.value,
    Intent.verify_answer.value,
    Intent.record_trace.value,
    Intent.challenge.value,
    Intent.metacognitive_feedback.value,
    Intent.proactive_intervention.value,
}

SUPPORTED_INTENTS = sorted(set(_IMPLEMENTED) | _MVP_PENDING)


class UnknownIntentError(ValueError):
    def __init__(self, intent: str) -> None:
        self.intent = intent
        self.supported = SUPPORTED_INTENTS
        super().__init__(f"unknown intent: {intent}")


def _not_implemented(req: AgentRequest) -> AgentResponse:
    settings = get_settings()
    return AgentResponse(
        request_id=req.request_id,
        task_id=req.task_id,
        status=ResponseStatus.failed,
        message=f"intent '{req.intent}' 已登记但尚未实现（A1 骨架仅支持 echo）",
        output={"intent": req.intent, "hint": "后续里程碑 A2/A3 将接入对应 Worker"},
        requires_approval=False,
        meta=ResponseMeta(agent_version=settings.agent_version, latency_ms=0),
    )


def dispatch(req: AgentRequest) -> AgentResponse:
    started = time.perf_counter()
    settings = get_settings()

    if req.intent in _IMPLEMENTED:
        resp = _IMPLEMENTED[req.intent](req)
    elif req.intent in _MVP_PENDING:
        resp = _not_implemented(req)
    else:
        raise UnknownIntentError(req.intent)

    latency_ms = int((time.perf_counter() - started) * 1000)
    resp.meta = ResponseMeta(
        agent_version=settings.agent_version,
        latency_ms=latency_ms,
    )
    return resp
