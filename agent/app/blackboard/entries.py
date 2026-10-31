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


def challenge_entry(
    *,
    entry_id: str,
    summary: str,
    evidence_refs: list[str] | None = None,
    severity: str = "medium",
) -> BlackboardEntry:
    return BlackboardEntry(
        entry_id=entry_id,
        type="challenge",
        summary=summary,
        severity=severity,
        evidence_refs=evidence_refs or [],
        status="open",
    )


def intervention_entry(
    *,
    entry_id: str,
    summary: str,
    evidence_refs: list[str] | None = None,
    severity: str = "medium",
) -> BlackboardEntry:
    return BlackboardEntry(
        entry_id=entry_id,
        type="intervention",
        summary=summary,
        severity=severity,
        evidence_refs=evidence_refs or [],
        status="open",
    )


def from_error_strategy(
    *,
    entry_id: str,
    blackboard_type: str,
    summary: str,
    evidence_refs: list[str] | None = None,
) -> BlackboardEntry:
    if blackboard_type == "intervention":
        return intervention_entry(
            entry_id=entry_id, summary=summary, evidence_refs=evidence_refs
        )
    if blackboard_type == "challenge":
        return challenge_entry(
            entry_id=entry_id, summary=summary, evidence_refs=evidence_refs
        )
    return conflict_entry(
        entry_id=entry_id, summary=summary, evidence_refs=evidence_refs
    )
