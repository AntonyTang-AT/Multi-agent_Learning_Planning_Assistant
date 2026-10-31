"""答辩三必演 + 增强演示目录（固定 examples）。"""

from __future__ import annotations

from typing import Any

# 三必演：冲突协商 / 校验弃答 / 错因差异
THREE_MUST: list[dict[str, Any]] = [
    {
        "id": "must_1_conflict",
        "title": "审计冲突协商",
        "example": "create_plan_final_review.json",
        "expect_status": "conflict",
        "checks": ["user_options", "blackboard_conflict"],
    },
    {
        "id": "must_2_abstain",
        "title": "校验弃答",
        "example": "verify_answer_force_fail.json",
        "expect_status": "abstain",
        "checks": ["hint_mode"],
    },
    {
        "id": "must_3_error_diff",
        "title": "错因驱动差异",
        "compare": [
            {
                "example": "create_plan_error_limit_misuse.json",
                "expect_status": "ok",
                "expect_action": "回顾概念",
            },
            {
                "example": "create_plan_error_symbol_error.json",
                "expect_status": "ok",
                "expect_action": "变式练习",
            },
        ],
    },
]

# 增强（有则演示）
ENHANCEMENTS: list[dict[str, Any]] = [
    {
        "id": "enh_challenge",
        "title": "结构化质疑",
        "example": "challenge_missing_assumption.json",
        "expect_status": "need_user",
    },
    {
        "id": "enh_metacog",
        "title": "元认知卡片",
        "example": "metacognitive_feedback.json",
        "expect_status": "ok",
    },
    {
        "id": "enh_intervention",
        "title": "主动干预",
        "example": "proactive_intervention_time_jump.json",
        "expect_status": "need_user",
    },
]
