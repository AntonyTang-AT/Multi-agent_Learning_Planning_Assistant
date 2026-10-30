"""POST /agent/v1/invoke"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.orchestrator.router import UnknownIntentError, SUPPORTED_INTENTS, dispatch
from app.schemas.request import AgentRequest
from app.schemas.response import AgentResponse

router = APIRouter(prefix="/agent/v1", tags=["invoke"])


@router.post("/invoke", response_model=AgentResponse)
def invoke(req: AgentRequest) -> AgentResponse:
    try:
        return dispatch(req)
    except UnknownIntentError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "unknown_intent",
                "message": f"不支持的 intent: {exc.intent}",
                "supported_intents": SUPPORTED_INTENTS,
            },
        ) from exc
