"""A1 调试回声 Worker：原样回传 input，便于联调 schema。"""

from __future__ import annotations

from app.schemas.request import AgentRequest
from app.schemas.response import AgentResponse, ResponseStatus


def handle(req: AgentRequest) -> AgentResponse:
    return AgentResponse(
        request_id=req.request_id,
        task_id=req.task_id,
        status=ResponseStatus.ok,
        message="echo ok",
        output={
            "echo": req.input,
            "scenario": req.scenario.value,
            "demo": req.demo.model_dump(),
            "resource_refs": [r.model_dump() for r in req.resource_refs],
        },
        requires_approval=False,
    )
