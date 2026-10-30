#!/usr/bin/env python3
"""Create labels, issues, and a GitHub Project board from github_issues.json."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "AntonyTang-AT/Multi-agent_Learning_Planning_Assistant"
OWNER = "AntonyTang-AT"
ISSUES_FILE = Path(__file__).with_name("github_issues.json")


def load_token() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("GITHUB_TOKEN="):
            os.environ["GH_TOKEN"] = line.split("=", 1)[1].strip()
            return


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(args))
    return subprocess.run(args, check=check, text=True, capture_output=True, encoding="utf-8")


def ensure_label(name: str, color: str, desc: str) -> None:
    p = run(
        ["gh", "label", "create", name, "--repo", REPO, "--color", color, "--description", desc],
        check=False,
    )
    if p.returncode != 0:
        run(
            ["gh", "label", "edit", name, "--repo", REPO, "--color", color, "--description", desc],
            check=False,
        )
    print(f"label ok: {name}")


def create_issue(title: str, body: str, labels: list[str]) -> int:
    body_file = Path(__file__).with_name("_tmp_issue_body.md")
    body_file.write_text(body, encoding="utf-8")
    cmd = ["gh", "issue", "create", "--repo", REPO, "--title", title, "--body-file", str(body_file)]
    for lab in labels:
        cmd.extend(["--label", lab])
    p = run(cmd)
    body_file.unlink(missing_ok=True)
    url = (p.stdout or "").strip()
    print(url)
    return int(url.rstrip("/").split("/")[-1])


def main() -> int:
    load_token()
    if not os.environ.get("GH_TOKEN"):
        print("GH_TOKEN missing", file=sys.stderr)
        return 1

    labels = [
        ("role:frontend", "1D76DB", "1号 前端"),
        ("role:backend", "0E8A16", "2号 后端"),
        ("role:agent", "5319E7", "3号 多智能体"),
        ("role:data", "FBCA04", "4号 资料"),
        ("role:pitch", "D93F0B", "5号 海报答辩"),
        ("role:meta", "BFDADC", "全组闸门/协作"),
        ("phase:pre-12", "C2E0C6", "12号检查点前"),
        ("phase:post-12", "FEF2C0", "12号检查点后"),
        ("phase:gate", "E99695", "进度闸门"),
        ("priority:P0", "B60205", "必做/演示关键"),
        ("priority:P1", "F9D0C4", "重要增强"),
        ("type:milestone", "0052CC", "可接取里程碑任务"),
    ]
    print("=== Labels ===")
    for name, color, desc in labels:
        ensure_label(name, color, desc)

    issues = json.loads(ISSUES_FILE.read_text(encoding="utf-8"))
    print(f"=== Issues ({len(issues)}) ===")
    numbers: list[int] = []
    for item in issues:
        n = create_issue(item["title"], item["body"], item["labels"])
        numbers.append(n)

    Path(__file__).with_name("_issue_numbers.txt").write_text(
        "\n".join(str(n) for n in numbers), encoding="utf-8"
    )

    print("=== Project ===")
    p = run(
        [
            "gh",
            "project",
            "create",
            "--owner",
            OWNER,
            "--title",
            "多智能体学习计划助手 · 开发看板",
            "--format",
            "json",
        ]
    )
    proj = json.loads(p.stdout)
    Path(__file__).with_name("_project.json").write_text(p.stdout, encoding="utf-8")
    number = proj["number"]
    print(f"Project #{number}: {proj.get('url')}")

    run(["gh", "project", "link", str(number), "--owner", OWNER, "--repo", REPO], check=False)

    for field_name, options in [
        ("角色", "前端,后端,Agent,资料,答辩,闸门"),
        ("阶段", "12号前,12号后,闸门"),
        ("优先级", "P0,P1"),
    ]:
        run(
            [
                "gh",
                "project",
                "field-create",
                str(number),
                "--owner",
                OWNER,
                "--name",
                field_name,
                "--data-type",
                "SINGLE_SELECT",
                "--single-select-options",
                options,
            ],
            check=False,
        )

    print("=== Add items ===")
    for n in numbers:
        run(
            [
                "gh",
                "project",
                "item-add",
                str(number),
                "--owner",
                OWNER,
                "--url",
                f"https://github.com/{REPO}/issues/{n}",
            ],
            check=False,
        )
        print(f"added #{n}")

    # Try set Status to Todo for all items via field-list + item-edit
    fields_p = run(
        ["gh", "project", "field-list", str(number), "--owner", OWNER, "--format", "json"],
        check=False,
    )
    if fields_p.returncode == 0 and fields_p.stdout:
        Path(__file__).with_name("_project_fields.json").write_text(fields_p.stdout, encoding="utf-8")

    print("DONE")
    print(f"Issues: https://github.com/{REPO}/issues")
    print(f"Project: {proj.get('url')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
