"""主 Agent：按 intent 路由到 Worker。"""

from __future__ import annotations

import time
from typing import Callable

from app.config import get_settings
from app.schemas.request import AgentRequest, Intent
from app.schemas.response import AgentResponse, ResponseMeta, ResponseStatus
from app.workers import arbitrate as arbitrate_worker
from app.workers import echo as echo_worker
from app.workers import evaluator as evaluator_worker
from app.workers import generator as generator_worker
from app.workers import planner as planner_worker
from app.workers import verifier as verifier_worker

Handler = Callable[[AgentRequest], AgentResponse]

_IMPLEMENTED: dict[str, Handler] = {
    Intent.echo.value: echo_worker.handle,
    Intent.create_plan.value: planner_worker.handle_create_plan,
    Intent.arbitrate.value: arbitrate_worker.handle_arbitrate,
    Intent.generate_question.value: generator_worker.handle_generate_question,
    Intent.verify_answer.value: verifier_worker.handle_verify_answer,
    Intent.challenge.value: evaluator_worker.handle_challenge,
    Intent.metacognitive_feedback.value: evaluator_worker.handle_metacognitive_feedback,
    Intent.proactive_intervention.value: evaluator_worker.handle_proactive_intervention,
}

_MVP_PENDING = {
    Intent.record_trace.value,
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
        message=f"intent '{req.intent}' 已登记但尚未实现",
        output={"intent": req.intent, "hint": "后续里程碑将接入对应 Worker"},
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
