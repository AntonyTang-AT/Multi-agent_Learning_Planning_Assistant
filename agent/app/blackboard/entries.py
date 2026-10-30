"""构造黑板条目（持久化由 backend 负责）。"""

from __future__ import annotations

from app.schemas.response import BlackboardEntry


def conflict_entry(
    *,
    entry_id: str,
    summary: str,
    evidence_refs: list[str] | None = None,
    severity: str = "high",
) -> BlackboardEntry:
    return BlackboardEntry(
        entry_id=entry_id,
        type="conflict",
        summary=summary,
        severity=severity,
        evidence_refs=evidence_refs or [],
        status="open",
    )
