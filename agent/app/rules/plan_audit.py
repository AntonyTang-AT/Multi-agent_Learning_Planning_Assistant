"""计划审计（确定性规则，非 LLM）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AuditIssue:
    day: int | None
    code: str
    summary: str
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class AuditResult:
    ok: bool
    issues: list[AuditIssue] = field(default_factory=list)

    @property
    def primary(self) -> AuditIssue | None:
        return self.issues[0] if self.issues else None


def _day_totals(tasks: list[dict[str, Any]]) -> dict[int, int]:
    totals: dict[int, int] = {}
    for t in tasks:
        day = int(t.get("day", 0))
        minutes = int(t.get("minutes", 0))
        totals[day] = totals.get(day, 0) + minutes
    return totals


def audit_plan(
    plan: dict[str, Any],
    *,
    daily_minutes: int,
    force_conflict: bool = False,
) -> AuditResult:
    tasks = list(plan.get("tasks") or [])
    issues: list[AuditIssue] = []

    if not tasks:
        issues.append(
            AuditIssue(
                day=None,
                code="empty_plan",
                summary="计划任务为空",
                evidence_refs=["plan#tasks"],
            )
        )
        return AuditResult(ok=False, issues=issues)

    for t in tasks:
        day = int(t.get("day", 0))
        if not str(t.get("completion_criteria") or "").strip():
            issues.append(
                AuditIssue(
                    day=day,
                    code="missing_completion_criteria",
                    summary=f"第{day}天任务缺少完成标准",
                    evidence_refs=[f"plan#day{day}"],
                )
            )

    totals = _day_totals(tasks)
    for day, total in sorted(totals.items()):
        if total > daily_minutes:
            issues.append(
                AuditIssue(
                    day=day,
                    code="daily_overload",
                    summary=f"计划第{day}天超出每日{daily_minutes}分钟预算（实际{total}分钟）",
                    evidence_refs=[f"plan#day{day}", "constraint#daily_minutes"],
                )
            )

    if force_conflict:
        # 演示短路：保证稳定出现第3天冲突叙事
        forced = AuditIssue(
            day=3,
            code="forced_conflict",
            summary=f"计划第3天超出每日{daily_minutes}分钟预算",
            evidence_refs=["plan#day3", "constraint#daily_minutes", "demo#force_conflict"],
        )
        # 放在最前，便于 message 对齐 examples
        issues = [forced] + [i for i in issues if i.code != "forced_conflict"]

    return AuditResult(ok=len(issues) == 0, issues=issues)
