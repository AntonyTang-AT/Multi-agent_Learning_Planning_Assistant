"""计算/符号校验（SymPy + 规则）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import sympy as sp
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


@dataclass
class VerifyResult:
    verdict: str  # passed | failed | doubt
    audit_trail: list[dict[str, Any]] = field(default_factory=list)
    diff: dict[str, Any] = field(default_factory=dict)
    message: str = ""


_TRANSFORMS = standard_transformations + (implicit_multiplication_application,)


def _parse(expr: str) -> sp.Expr:
    return parse_expr(str(expr), transformations=_TRANSFORMS)


def _as_number(value: Any) -> float | None:
    try:
        return float(sp.N(value))
    except Exception:
        return None


def verify_with_hint(
    *,
    proposed_answer: str | None,
    verify_hint: dict[str, Any] | None,
    expected: str | None = None,
    force_fail: bool = False,
) -> VerifyResult:
    trail: list[dict[str, Any]] = []

    if force_fail:
        trail.append(
            {
                "step": "demo_force_verify_fail",
                "result": "failed",
                "detail": "demo.force_verify_fail=true，强制走弃答演示路径",
            }
        )
        return VerifyResult(
            verdict="failed",
            audit_trail=trail,
            diff={"reason": "forced_fail"},
            message="演示开关强制校验失败",
        )

    hint = verify_hint or {}
    expected_raw = expected if expected is not None else hint.get("expected")
    expr_raw = hint.get("expr")

    if proposed_answer is None and expected_raw is None and not expr_raw:
        trail.append({"step": "input_check", "result": "doubt", "detail": "缺少可校验字段"})
        return VerifyResult(
            verdict="doubt",
            audit_trail=trail,
            message="缺少 answer / verify_hint，无法可靠校验",
        )

    # 1) 若有 expr，用 SymPy 求值并与 expected / proposed 比对
    computed: Any = None
    if expr_raw:
        try:
            computed = sp.simplify(_parse(str(expr_raw)))
            trail.append(
                {
                    "step": "sympy_eval",
                    "result": "ok",
                    "detail": f"expr={expr_raw} -> {computed}",
                }
            )
        except Exception as exc:  # noqa: BLE001
            trail.append(
                {
                    "step": "sympy_eval",
                    "result": "failed",
                    "detail": f"表达式解析/求值失败: {exc}",
                }
            )
            return VerifyResult(
                verdict="failed",
                audit_trail=trail,
                diff={"expr": expr_raw, "error": str(exc)},
                message="符号校验失败",
            )

    target = expected_raw if expected_raw is not None else proposed_answer
    candidate = proposed_answer if proposed_answer is not None else (
        str(computed) if computed is not None else None
    )

    if target is None or candidate is None:
        trail.append({"step": "compare", "result": "doubt", "detail": "比对双方不完整"})
        return VerifyResult(verdict="doubt", audit_trail=trail, message="无法完成比对")

    # 数值比对
    t_num = _as_number(target)
    c_num = _as_number(candidate)
    if computed is not None:
        comp_num = _as_number(computed)
        if expected_raw is not None and comp_num is not None and t_num is not None:
            if abs(comp_num - t_num) < 1e-9:
                trail.append({"step": "numeric_compare", "result": "passed", "detail": "expr≈expected"})
            else:
                trail.append(
                    {
                        "step": "numeric_compare",
                        "result": "failed",
                        "detail": f"expr={comp_num} expected={t_num}",
                    }
                )
                return VerifyResult(
                    verdict="failed",
                    audit_trail=trail,
                    diff={"computed": str(computed), "expected": str(expected_raw)},
                    message="计算结果与期望不一致",
                )

    if t_num is not None and c_num is not None:
        ok = abs(t_num - c_num) < 1e-9
        trail.append(
            {
                "step": "numeric_compare_answer",
                "result": "passed" if ok else "failed",
                "detail": f"candidate={c_num} target={t_num}",
            }
        )
        if ok:
            return VerifyResult(verdict="passed", audit_trail=trail, message="校验通过")
        return VerifyResult(
            verdict="failed",
            audit_trail=trail,
            diff={"candidate": str(candidate), "expected": str(target)},
            message="答案与期望数值不一致",
        )

    # 符号简化比对
    try:
        left = _parse(str(candidate))
        right = _parse(str(target))
        diff_expr = sp.simplify(left - right)
        ok = diff_expr == 0
        trail.append(
            {
                "step": "symbolic_compare",
                "result": "passed" if ok else "failed",
                "detail": f"simplify(candidate-target)={diff_expr}",
            }
        )
        if ok:
            return VerifyResult(verdict="passed", audit_trail=trail, message="符号校验通过")
        return VerifyResult(
            verdict="failed",
            audit_trail=trail,
            diff={"candidate": str(candidate), "expected": str(target), "diff": str(diff_expr)},
            message="符号答案不一致",
        )
    except Exception as exc:  # noqa: BLE001
        # 退回字符串规范化
        norm_c = str(candidate).strip().lower().replace(" ", "")
        norm_t = str(target).strip().lower().replace(" ", "")
        ok = norm_c == norm_t
        trail.append(
            {
                "step": "string_fallback",
                "result": "passed" if ok else "failed",
                "detail": f"sympy_error={exc}; string_equal={ok}",
            }
        )
        if ok:
            return VerifyResult(verdict="passed", audit_trail=trail, message="文本比对通过")
        return VerifyResult(
            verdict="failed",
            audit_trail=trail,
            diff={"candidate": str(candidate), "expected": str(target)},
            message="无法可靠完成符号校验",
        )


def handle_verify_answer(req: Any) -> Any:
    """intent=verify_answer 入口。"""
    from app.schemas.response import AgentResponse, ResponseStatus

    data = req.input or {}
    question = data.get("question") if isinstance(data.get("question"), dict) else {}
    proposed = data.get("answer")
    if proposed is None:
        proposed = question.get("answer")
    verify_hint = data.get("verify_hint") or question.get("verify_hint")
    expected = data.get("expected")
    if expected is None and isinstance(question, dict):
        expected = question.get("answer") if verify_hint else question.get("answer")

    result = verify_with_hint(
        proposed_answer=None if proposed is None else str(proposed),
        verify_hint=verify_hint if isinstance(verify_hint, dict) else None,
        expected=None if expected is None else str(expected),
        force_fail=bool(req.demo.force_verify_fail),
    )

    if result.verdict == "passed":
        return AgentResponse(
            request_id=req.request_id,
            task_id=req.task_id,
            status=ResponseStatus.ok,
            message=result.message or "校验通过",
            output={
                "verdict": "passed",
                "diff": result.diff,
                "audit_trail": result.audit_trail,
            },
        )

    if result.verdict == "doubt":
        return AgentResponse(
            request_id=req.request_id,
            task_id=req.task_id,
            status=ResponseStatus.doubt,
            message=result.message or "校验存疑",
            output={
                "verdict": "doubt",
                "diff": result.diff,
                "audit_trail": result.audit_trail,
            },
            requires_approval=True,
        )

    # failed → 不硬给错答，给出提示/弃答语义（verify 场景用 abstain）
    return AgentResponse(
        request_id=req.request_id,
        task_id=req.task_id,
        status=ResponseStatus.abstain,
        message="校验未通过，暂不以不可靠结论作为正确答案",
        output={
            "verdict": "failed",
            "diff": result.diff,
            "audit_trail": result.audit_trail,
            "hint_mode": True,
            "hint": "请复查计算步骤，或补充定义域/假设后再提交",
        },
        requires_approval=True,
    )
