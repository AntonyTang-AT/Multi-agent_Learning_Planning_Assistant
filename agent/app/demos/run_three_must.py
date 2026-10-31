"""一键跑答辩三必演（及可选增强），不依赖外部服务进程。

用法（在 agent/ 目录）：
  python -m app.demos.run_three_must
  python -m app.demos.run_three_must --with-enhancements
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from app.demos.catalog import ENHANCEMENTS, THREE_MUST
from app.orchestrator.router import dispatch
from app.schemas.request import AgentRequest

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


def _load_request(example_name: str) -> dict[str, Any]:
    path = EXAMPLES_DIR / example_name
    data = json.loads(path.read_text(encoding="utf-8"))
    if "request" not in data:
        raise KeyError(f"{example_name} missing request")
    return data["request"]


def _invoke(example_name: str) -> dict[str, Any]:
    req = AgentRequest.model_validate(_load_request(example_name))
    resp = dispatch(req)
    return resp.model_dump()


def _check_single(item: dict[str, Any]) -> tuple[bool, str]:
    body = _invoke(item["example"])
    status = body.get("status")
    if status != item["expect_status"]:
        return False, f"{item['id']}: status={status} expected={item['expect_status']}"

    checks = item.get("checks") or []
    if "user_options" in checks and len(body.get("user_options") or []) < 3:
        return False, f"{item['id']}: user_options < 3"
    if "blackboard_conflict" in checks:
        types = {e.get("type") for e in body.get("blackboard_entries") or []}
        if "conflict" not in types:
            return False, f"{item['id']}: missing conflict blackboard"
    if "hint_mode" in checks and not (body.get("output") or {}).get("hint_mode"):
        return False, f"{item['id']}: missing hint_mode"

    return True, f"{item['id']}: OK ({item['title']})"


def _check_compare(item: dict[str, Any]) -> tuple[bool, str]:
    results = []
    for part in item["compare"]:
        body = _invoke(part["example"])
        if body.get("status") != part["expect_status"]:
            return (
                False,
                f"{item['id']}: {part['example']} status={body.get('status')}",
            )
        action = ((body.get("output") or {}).get("error_strategy") or {}).get("action")
        if action != part["expect_action"]:
            return (
                False,
                f"{item['id']}: action={action} expected={part['expect_action']}",
            )
        results.append(action)
    if len(set(results)) < 2:
        return False, f"{item['id']}: strategies not differentiated"
    return True, f"{item['id']}: OK ({item['title']}) actions={results}"


def run(with_enhancements: bool = False) -> int:
    print("=== 三必演 ===")
    failed = 0
    for item in THREE_MUST:
        if item.get("compare"):
            ok, msg = _check_compare(item)
        else:
            ok, msg = _check_single(item)
        print(("PASS " if ok else "FAIL ") + msg)
        if not ok:
            failed += 1

    if with_enhancements:
        print("=== 增强演示 ===")
        for item in ENHANCEMENTS:
            ok, msg = _check_single(item)
            print(("PASS " if ok else "FAIL ") + msg)
            if not ok:
                failed += 1

    if failed:
        print(f"\n{failed} demo(s) failed")
        return 1
    print("\nAll demos passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run fixed defense demos")
    parser.add_argument(
        "--with-enhancements",
        action="store_true",
        help="also run challenge / metacog / intervention demos",
    )
    args = parser.parse_args(argv)
    return run(with_enhancements=args.with_enhancements)


if __name__ == "__main__":
    raise SystemExit(main())
