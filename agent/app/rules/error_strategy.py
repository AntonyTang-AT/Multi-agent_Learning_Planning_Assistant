"""错因 → 复习/计划插入策略（规则表，无 Key 可演示）。

对齐资料样例中的 error_tags，并额外覆盖先修回炉类错因。
"""

from __future__ import annotations

from typing import Any

# ≥4 种错因；与 data/questions 中出现的标签对齐 + 扩展
ERROR_STRATEGIES: dict[str, dict[str, Any]] = {
    "limit_misuse": {
        "strategy_id": "review_limit_rules",
        "action": "回顾概念",
        "object_template": "{label}：极限运算法则与常见误用辨析",
        "minutes": 25,
        "completion_criteria": "写出 2 个典型误用反例并订正",
        "load": "medium",
        "insert": "front",
        "blackboard_type": "challenge",
        "summary_template": "检测到错因 limit_misuse：建议先挑战极限运算法则理解，再继续刷题",
        "recommendation": "先做概念辨析卡，再做变式填空",
    },
    "symbol_error": {
        "strategy_id": "drill_symbol_variants",
        "action": "变式练习",
        "object_template": "{label}：符号与表达式变形专项",
        "minutes": 30,
        "completion_criteria": "完成 3 道符号变形题且自检无笔误",
        "load": "medium",
        "insert": "after_first",
        "blackboard_type": "intervention",
        "summary_template": "检测到错因 symbol_error：主动插入符号变形干预块",
        "recommendation": "放慢书写，逐步展开表达式后再求极限/导数",
    },
    "undefined_assumption": {
        "strategy_id": "clarify_assumptions",
        "action": "补全假设",
        "object_template": "{label}：定义域与隐含假设检查清单",
        "minutes": 20,
        "completion_criteria": "列出本题全部隐含假设并判断是否满足",
        "load": "low",
        "insert": "front",
        "blackboard_type": "challenge",
        "summary_template": "检测到错因 undefined_assumption：结构化质疑假设是否完备",
        "recommendation": "先写假设清单，再动笔计算",
    },
    "conceptual_gap": {
        "strategy_id": "prerequisite_rollback",
        "action": "先修回炉",
        "object_template": "{label}：先修知识点回炉（低门槛任务）",
        "minutes": 35,
        "completion_criteria": "完成先修回顾卡 + 2 道基础题",
        "load": "low",
        "insert": "front",
        "blackboard_type": "intervention",
        "summary_template": "检测到错因 conceptual_gap：建议回退先修后再推进",
        "recommendation": "暂停拔高题，回到先修定义与例题",
    },
}


def list_error_tags() -> list[str]:
    return sorted(ERROR_STRATEGIES.keys())


def get_strategy(error_tag: str) -> dict[str, Any] | None:
    return ERROR_STRATEGIES.get(error_tag)


def build_remediation_task(
    *,
    error_tag: str,
    knowledge_id: str,
    label: str,
    subject: str = "math",
    day: int = 1,
) -> dict[str, Any] | None:
    strategy = get_strategy(error_tag)
    if not strategy:
        return None
    return {
        "day": day,
        "action": strategy["action"],
        "object": strategy["object_template"].format(label=label),
        "minutes": strategy["minutes"],
        "completion_criteria": strategy["completion_criteria"],
        "load": strategy["load"],
        "knowledge_ids": [knowledge_id],
        "subject": subject,
        "error_tag": error_tag,
        "strategy_id": strategy["strategy_id"],
        "remediation": True,
    }
