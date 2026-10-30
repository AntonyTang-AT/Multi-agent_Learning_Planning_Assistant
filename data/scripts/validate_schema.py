"""Minimal schema check for data/ JSON packs. Expand as fields stabilize."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_QUESTION_FIELDS = {
    "question_id",
    "subject",
    "knowledge_ids",
    "scenario_tags",
    "difficulty",
    "type",
    "stem",
    "answer",
    "source",
    "license_note",
}


def check_outline(path: Path) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    if "nodes" not in data:
        errors.append(f"{path.name}: missing nodes")
        return errors
    for node in data["nodes"]:
        if "id" not in node or "name" not in node:
            errors.append(f"{path.name}: node missing id/name")
    return errors


def check_questions(path: Path) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    for q in data.get("questions", []):
        missing = REQUIRED_QUESTION_FIELDS - set(q)
        if missing:
            errors.append(f"{path.name}:{q.get('question_id')}: missing {sorted(missing)}")
    return errors


def main() -> int:
    errors: list[str] = []
    for p in (ROOT / "taxonomy").glob("*.json"):
        errors.extend(check_outline(p))
    for p in (ROOT / "questions").glob("*.json"):
        errors.extend(check_questions(p))
    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
