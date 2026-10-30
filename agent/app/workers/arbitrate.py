"""用户裁决后重排计划。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.rules.constraints import parse_daily_minutes
from app.rules.plan_audit import audit_plan
from app.schemas.request import AgentRequest
from app.schemas.response import AgentResponse, ResponseStatus


def _extract_plan(req: AgentRequest) -> dict[str, Any] | None:
    plan = req.input.get("plan")
    if isinstance(plan, dict) and isinstance(plan.get("tasks"), list):
        return deepcopy(plan)
    # 兼容嵌套 output.plan
    output = req.input.get("output")
    if isinstance(output, dict) and isinstance(output.get("plan"), dict):
        return deepcopy(output["plan"])
    return None


def _apply_option(plan: dict[str, Any], option_id: str, daily: int) -> tuple[dict[str, Any], int, str]:
    tasks = list(plan.get("tasks") or [])
    new_daily = daily
    note = ""

    if option_id == "extend_time":
        # 抬高预算到覆盖当前最大日负荷 + 缓冲
        max_day = 0
        for t in tasks:
            max_day = max(max_day, int(t.get("minutes", 0)))
        new_daily = max(daily, max_day + 10)
        plan["daily_minutes_budget"] = new_daily
        note = f"已按选项 extend_time 将每日预算调整为 {new_daily} 分钟"
    elif option_id == "reduce_depth":
        for t in tasks:
            mins = int(t.get("minutes", 0))
            t["minutes"] = max(20, int(mins * 0.6))
            t["load"] = "low"
            criteria = str(t.get("completion_criteria") or "")
            if "3道" in criteria:
                t["completion_criteria"] = criteria.replace("3道", "1道")
        plan["tasks"] = tasks
        note = "已按选项 reduce_depth 降低每日任务时长与深度"
    elif option_id == "adjust_goal":
        # 保留前半段任务，缩短跨度
        keep = max(1, len(tasks) // 2)
        plan["tasks"] = tasks[:keep]
        plan["goal"] = f"{plan.get('goal', '复习')}（已降级目标）"
        note = "已按选项 adjust_goal 缩短计划跨度并降级目标"
    else:
        note = f"未知 option_id={option_id}，原样返回并重新审计"

    plan["arbitration"] = {"option_id": option_id, "note": note}
    return plan, new_daily, note


def handle_arbitrate(req: AgentRequest) -> AgentResponse:
    option_id = str(req.input.get("option_id") or "").strip()
    if not option_id:
        return AgentResponse(
            request_id=req.request_id,
            task_id=req.task_id,
            status=ResponseStatus.failed,
            message="arbitrate 需要 input.option_id",
            output={},
        )

    plan = _extract_plan(req)
    if plan is None:
        return AgentResponse(
            request_id=req.request_id,
            task_id=req.task_id,
            status=ResponseStatus.failed,
            message="arbitrate 需要 input.plan（或 input.output.plan）",
            output={"option_id": option_id},
        )

    hard = req.user_profile.constraints.hard
    daily = parse_daily_minutes(hard)
    plan, new_daily, note = _apply_option(plan, option_id, daily)

    # 裁决后不再 force_conflict，避免演示死循环
    audit = audit_plan(plan, daily_minutes=new_daily, force_conflict=False)
    if not audit.ok:
        primary = audit.primary
        return AgentResponse(
            request_id=req.request_id,
            task_id=req.task_id,
            status=ResponseStatus.conflict,
            message=(primary.summary if primary else "裁决后仍存在冲突"),
            output={"plan": plan, "audit_issues": [i.__dict__ for i in audit.issues]},
            requires_approval=True,
        )

    return AgentResponse(
        request_id=req.request_id,
        task_id=req.task_id,
        status=ResponseStatus.ok,
        message=note or "裁决完成，计划已通过审计",
        output={"plan": plan},
        requires_approval=True,
    )
