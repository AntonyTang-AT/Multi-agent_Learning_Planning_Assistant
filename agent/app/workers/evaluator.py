"""评估侧：结构化质疑 / 元认知卡片 / 主动干预（模板，无 Key 可演示）。"""

from __future__ import annotations

from typing import Any

from app.blackboard.entries import challenge_entry, intervention_entry
from app.schemas.request import AgentRequest
from app.schemas.response import AgentResponse, ResponseStatus, UserOption


def _question_from_req(req: AgentRequest) -> dict[str, Any]:
    data = req.input or {}
    q = data.get("question")
    if isinstance(q, dict):
        return q
    payload = req.resource_payload or {}
    samples = payload.get("sample_questions")
    if isinstance(samples, list) and samples and isinstance(samples[0], dict):
        return samples[0]
    return {}


def handle_challenge(req: AgentRequest) -> AgentResponse:
    """对接缺假设题：assumptions 为空或显式 force 时发出结构化质疑。"""
    q = _question_from_req(req)
    assumptions = q.get("assumptions")
    missing = not isinstance(assumptions, list) or len(assumptions) == 0
    force = bool((req.input or {}).get("force_challenge"))

    if not missing and not force:
        return AgentResponse(
            request_id=req.request_id,
            task_id=req.task_id,
            status=ResponseStatus.ok,
            message="假设字段已提供，无需额外质疑",
            output={
                "challenge": None,
                "question_id": q.get("question_id"),
                "assumptions": assumptions,
            },
        )

    stem = q.get("stem") or (req.input or {}).get("stem") or "（未提供题干）"
    card = {
        "type": "structured_challenge",
        "title": "假设是否完备？",
        "prompt": (
            f"题目「{stem}」未给出完整假设。"
            "请先判断定义域、单侧极限/连续性等隐含条件是否成立，再继续作答。"
        ),
        "checklist": [
            "定义域是否包含求解点？",
            "是否需要单侧极限或额外连续性假设？",
            "答案是否依赖未声明约定？",
        ],
    }
    options = [
        UserOption(id="add_assumptions", label="补充假设后再算"),
        UserOption(id="hint_mode", label="先看提示，不直接看答案"),
        UserOption(id="skip_question", label="跳过本题，换可校验题"),
    ]
    bb = challenge_entry(
        entry_id=f"bb_{req.request_id}_challenge",
        summary="缺假设题触发结构化质疑：请先补全假设",
        evidence_refs=[
            f"question#{q.get('question_id', 'unknown')}",
            "assumption#missing",
        ],
    )
    return AgentResponse(
        request_id=req.request_id,
        task_id=req.task_id,
        status=ResponseStatus.need_user,
        message="检测到缺假设，已发起结构化质疑",
        output={"card": card, "challenge": card, "question": q or None},
        blackboard_entries=[bb],
        user_options=options,
        requires_approval=True,
    )


def handle_metacognitive_feedback(req: AgentRequest) -> AgentResponse:
    """元认知卡片：引导复盘，不生成答案。"""
    error_tag = (req.input or {}).get("error_tag") or "general"
    topic = (req.input or {}).get("topic") or (
        req.resource_refs[0].label if req.resource_refs else "当前知识点"
    )
    card = {
        "type": "metacognitive",
        "title": "学习复盘",
        "topic": topic,
        "error_tag": error_tag,
        "questions": [
            "刚才卡在哪一步？是概念、变形还是计算？",
            "如果重做一遍，你会先写哪三条检查项？",
            "这道题与上周错题是否同类？",
        ],
        "options": [
            {"id": "write_checklist", "label": "写下检查清单"},
            {"id": "retry_similar", "label": "再做一道同类题"},
            {"id": "review_concept", "label": "先回看概念卡"},
        ],
    }
    return AgentResponse(
        request_id=req.request_id,
        task_id=req.task_id,
        status=ResponseStatus.ok,
        message="已生成元认知复盘卡片",
        output={"card": card},
        requires_approval=False,
    )


def handle_proactive_intervention(req: AgentRequest) -> AgentResponse:
    """主动干预：时间跳跃 / 高负荷信号 → 干预卡片。"""
    jump = int(req.demo.time_jump_days or (req.input or {}).get("time_jump_days") or 0)
    load = ((req.trace_snapshot or {}).get("load_signals") or {})
    overload = bool(load.get("overload")) or jump >= 2

    if not overload and jump <= 0:
        return AgentResponse(
            request_id=req.request_id,
            task_id=req.task_id,
            status=ResponseStatus.ok,
            message="暂无明显干预触发条件",
            output={"card": None, "triggered": False},
        )

    reason = (
        f"检测到时间跳跃 {jump} 天，学习计划可能脱节"
        if jump >= 2
        else "检测到负荷信号过高，建议主动降载"
    )
    card = {
        "type": "proactive_intervention",
        "title": "主动干预建议",
        "reason": reason,
        "suggestions": [
            "将今日任务降为低负荷回顾",
            "把拔高题推迟到恢复节奏后",
            "用 15 分钟先修回炉重启",
        ],
        "options": [
            {"id": "downgrade_today", "label": "降低今日深度"},
            {"id": "catch_up_tomorrow", "label": "明天补一段短计划"},
            {"id": "keep_going", "label": "维持原计划（自行负责）"},
        ],
    }
    bb = intervention_entry(
        entry_id=f"bb_{req.request_id}_intervention",
        summary=reason,
        evidence_refs=["demo#time_jump" if jump else "trace#load_signals"],
    )
    return AgentResponse(
        request_id=req.request_id,
        task_id=req.task_id,
        status=ResponseStatus.need_user,
        message="已触发主动干预卡片",
        output={"card": card, "triggered": True},
        blackboard_entries=[bb],
        user_options=[
            UserOption(id=o["id"], label=o["label"]) for o in card["options"]
        ],
        requires_approval=True,
    )
