"""计划草案生成（规则/模板优先，无 Key 可演示）。"""

from __future__ import annotations

from typing import Any

from app.blackboard.entries import conflict_entry
from app.rules.constraints import parse_daily_minutes, parse_days_left, parse_subject
from app.rules.plan_audit import audit_plan
from app.schemas.request import AgentRequest, Scenario
from app.schemas.response import AgentResponse, ResponseStatus, UserOption

DEFAULT_USER_OPTIONS = [
    UserOption(id="extend_time", label="延长每日学习时间"),
    UserOption(id="reduce_depth", label="降低复习深度"),
    UserOption(id="adjust_goal", label="调整目标"),
]

_TOPIC_FALLBACK = [
    ("math.limit", "极限与连续", "极限定义与运算法则"),
    ("math.derivative", "导数与微分", "导数定义与基本求导"),
    ("math.integral", "积分", "不定积分基本公式"),
    ("math.series", "级数", "级数收敛性判别"),
]


def _topics_from_request(req: AgentRequest) -> list[tuple[str, str, str]]:
    topics: list[tuple[str, str, str]] = []
    for ref in req.resource_refs:
        kid = ref.id
        label = ref.label or kid
        object_name = label
        topics.append((kid, label, object_name))
    if not topics:
        return list(_TOPIC_FALLBACK)
    return topics


def _base_minutes(scenario: Scenario, daily_minutes: int) -> int:
    if scenario == Scenario.catch_up:
        return min(35, max(20, daily_minutes // 3))
    return min(50, max(25, int(daily_minutes * 0.7)))


def build_plan_draft(req: AgentRequest) -> dict[str, Any]:
    hard = req.user_profile.constraints.hard
    daily = parse_daily_minutes(hard)
    days_left = parse_days_left(req.input)
    subject = parse_subject(hard)
    topics = _topics_from_request(req)
    minutes = _base_minutes(req.scenario, daily)

    tasks: list[dict[str, Any]] = []
    # 覆盖前若干天；不足天数则循环知识点
    span = min(days_left, max(3, len(topics) + 1))
    for i in range(span):
        day = i + 1
        kid, label, object_name = topics[i % len(topics)]
        if req.scenario == Scenario.catch_up:
            action = "补漏"
            criteria = f"完成「{label}」概念回顾卡 + 2道基础题"
            load = "low"
        else:
            action = "复习"
            criteria = f"完成3道「{label}」基础填空"
            load = "medium" if minutes <= 45 else "high"

        task_minutes = minutes
        # 若预算很紧，仍用模板分钟，交给 audit 暴露冲突；force 时再抬高第3天
        if req.demo.force_conflict and day == 3:
            task_minutes = max(daily + 15, minutes + 20)

        tasks.append(
            {
                "day": day,
                "action": action,
                "object": object_name,
                "minutes": task_minutes,
                "completion_criteria": criteria,
                "load": load,
                "knowledge_ids": [kid],
                "subject": subject,
            }
        )

    return {
        "scenario": req.scenario.value,
        "goal": req.input.get("goal") or ("跟课补漏" if req.scenario == Scenario.catch_up else "期末复习"),
        "daily_minutes_budget": daily,
        "days_left": days_left,
        "tasks": tasks,
    }


def handle_create_plan(req: AgentRequest) -> AgentResponse:
    hard = req.user_profile.constraints.hard
    daily = parse_daily_minutes(hard)
    plan = build_plan_draft(req)
    audit = audit_plan(plan, daily_minutes=daily, force_conflict=req.demo.force_conflict)

    if audit.ok:
        return AgentResponse(
            request_id=req.request_id,
            task_id=req.task_id,
            status=ResponseStatus.ok,
            message="计划草案已通过审计",
            output={"plan": plan},
            requires_approval=True,
        )

    primary = audit.primary
    assert primary is not None
    entry = conflict_entry(
        entry_id=f"bb_{req.request_id}_conflict",
        summary=primary.summary,
        evidence_refs=primary.evidence_refs,
    )
    return AgentResponse(
        request_id=req.request_id,
        task_id=req.task_id,
        status=ResponseStatus.conflict,
        message=primary.summary,
        output={"plan": plan, "audit_issues": [i.__dict__ for i in audit.issues]},
        blackboard_entries=[entry],
        user_options=list(DEFAULT_USER_OPTIONS),
        requires_approval=True,
    )
