"""从 hard constraints / input 解析预算与天数。"""

from __future__ import annotations

import re
from typing import Any


_DAILY_RE = re.compile(r"daily_minutes\s*<=\s*(\d+)", re.I)
_EXAM_RE = re.compile(r"exam_date\s*=\s*([0-9-]+)", re.I)
_SUBJECT_RE = re.compile(r"subject\s*=\s*([a-zA-Z_]+)", re.I)


def parse_daily_minutes(hard: list[str], default: int = 120) -> int:
    for item in hard:
        m = _DAILY_RE.search(item)
        if m:
            return int(m.group(1))
    return default


def parse_exam_date(hard: list[str]) -> str | None:
    for item in hard:
        m = _EXAM_RE.search(item)
        if m:
            return m.group(1)
    return None


def parse_subject(hard: list[str], default: str = "math") -> str:
    for item in hard:
        m = _SUBJECT_RE.search(item)
        if m:
            return m.group(1).lower()
    return default


def parse_days_left(input_data: dict[str, Any], default: int = 14) -> int:
    raw = input_data.get("days_left")
    if raw is None:
        return default
    try:
        return max(1, int(raw))
    except (TypeError, ValueError):
        return default
