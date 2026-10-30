"""出题 Worker：优先 resource_payload，失败走重试→提示→abstain。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.schemas.request import AgentRequest
from app.schemas.response import AgentResponse, ResponseStatus
from app.workers.verifier import VerifyResult, verify_with_hint

_TEMPLATES: list[dict[str, Any]] = [
    {
        "question_id": "gen_limit_sinc",
        "subject": "math",
        "knowledge_ids": ["math.limit"],
        "type": "fill",
        "stem": "求 lim(x→0) sin(x)/x 的值。",
        "answer": "1",
        "assumptions": [],
        "error_tags": ["limit_misuse"],
        "verify_hint": {"expr": "limit(sin(x)/x, x, 0)", "expected": "1"},
    },
    {
        "question_id": "gen_deriv_x2",
        "subject": "math",
        "knowledge_ids": ["math.derivative"],
        "type": "fill",
        "stem": "求 d/dx (x**2) 在任意 x 处的导数表达式。",
        "answer": "2*x",
        "assumptions": [],
        "error_tags": ["symbol_error"],
        "verify_hint": {"expr": "diff(x**2, x)", "expected": "2*x"},
    },
]


def _pick_from_payload(req: AgentRequest) -> dict[str, Any] | None:
    payload = req.resource_payload or {}
    samples = payload.get("sample_questions")
    if isinstance(samples, list) and samples:
        q = samples[0]
        if isinstance(q, dict) and q.get("stem"):
            return deepcopy(q)
    return None


def _pick_template(req: AgentRequest) -> dict[str, Any]:
    kids = [r.id for r in req.resource_refs]
    for tpl in _TEMPLATES:
        if any(k in tpl.get("knowledge_ids", []) for k in kids):
            return deepcopy(tpl)
    # input 指定 knowledge_id
    kid = (req.input or {}).get("knowledge_id")
    if kid:
        for tpl in _TEMPLATES:
            if kid in tpl.get("knowledge_ids", []):
                return deepcopy(tpl)
    return deepcopy(_TEMPLATES[0])


def _broken_variant(question: dict[str, Any]) -> dict[str, Any]:
    """构造必然校验失败的变体（用于重试后仍失败 / 演示）。"""
    q = deepcopy(question)
    q["answer"] = "__invalid_unverified__"
    hint = dict(q.get("verify_hint") or {})
    if "expected" in hint:
        hint["expected"] = "__not_equal__"
    q["verify_hint"] = hint
    q["question_id"] = f"{q.get('question_id', 'q')}_broken"
    return q


def _check_question(question: dict[str, Any], *, force_fail: bool) -> VerifyResult:
    return verify_with_hint(
        proposed_answer=str(question.get("answer")) if question.get("answer") is not None else None,
        verify_hint=question.get("verify_hint") if isinstance(question.get("verify_hint"), dict) else None,
        expected=(
            str(question["verify_hint"]["expected"])
            if isinstance(question.get("verify_hint"), dict)
            and question["verify_hint"].get("expected") is not None
            else None
        ),
        force_fail=force_fail,
    )


def _abstain_response(
    req: AgentRequest,
    *,
    trail: list[dict[str, Any]],
    draft: dict[str, Any] | None,
    reason: str,
) -> AgentResponse:
    return AgentResponse(
        request_id=req.request_id,
        task_id=req.task_id,
        status=ResponseStatus.abstain,
        message="出题校验未通过，系统弃答：不返回不可靠答案",
        output={
            "verdict": "failed",
            "question": None,
            "draft_discarded": draft,
            "audit_trail": trail,
            "hint_mode": True,
            "hint": "可改用已入库且带 verify_hint 的题目，或降低生成复杂度后重试",
            "reason": reason,
        },
        requires_approval=True,
    )


def handle_generate_question(req: AgentRequest) -> AgentResponse:
    force_fail = bool(req.demo.force_verify_fail)
    trail: list[dict[str, Any]] = []

    # Attempt 1: payload 或模板
    q1 = _pick_from_payload(req) or _pick_template(req)
    trail.append({"step": "generate_attempt_1", "result": "ok", "detail": q1.get("question_id")})
    v1 = _check_question(q1, force_fail=force_fail)
    trail.extend(v1.audit_trail)

    if v1.verdict == "passed" and not force_fail:
        return AgentResponse(
            request_id=req.request_id,
            task_id=req.task_id,
            status=ResponseStatus.ok,
            message="已生成并通过校验的题目",
            output={
                "question": q1,
                "verdict": "passed",
                "audit_trail": trail,
            },
        )

    # Attempt 2: 降级为更简单模板（若第一次已是模板且 force，则仍走失败）
    q2 = deepcopy(_TEMPLATES[0])
    trail.append({"step": "generate_attempt_2_retry", "result": "ok", "detail": q2.get("question_id")})
    v2 = _check_question(q2, force_fail=force_fail)
    trail.extend(v2.audit_trail)

    if v2.verdict == "passed" and not force_fail:
        return AgentResponse(
            request_id=req.request_id,
            task_id=req.task_id,
            status=ResponseStatus.ok,
            message="重试后生成并通过校验的题目",
            output={
                "question": q2,
                "verdict": "passed",
                "audit_trail": trail,
                "degraded": True,
            },
        )

    # 最终弃答：不返回错误答案当正解
    trail.append(
        {
            "step": "abstain",
            "result": "abstain",
            "detail": "重试后仍未通过校验，或 force_verify_fail 演示",
        }
    )
    discarded = _broken_variant(q1) if force_fail else q1
    return _abstain_response(
        req,
        trail=trail,
        draft=discarded,
        reason="verify_failed_after_retry" if not force_fail else "force_verify_fail",
    )
