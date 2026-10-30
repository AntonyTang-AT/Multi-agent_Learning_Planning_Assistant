#!/usr/bin/env python3
"""Assign Agent issues already done via gh; set Project Status -> In Progress."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "AntonyTang-AT/Multi-agent_Learning_Planning_Assistant"
PROJECT_ID = "PVT_kwHOBU1eIc4BpdPU"
TARGET_NUMBERS = {4, 16, 17, 18, 19, 20}


def load_token() -> None:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("GITHUB_TOKEN="):
            os.environ["GH_TOKEN"] = line.split("=", 1)[1].strip()
            os.environ.pop("GITHUB_TOKEN", None)
            return


def gh_api(input_obj: dict) -> dict:
    tmp = Path(__file__).with_name("_gql_input.json")
    tmp.write_text(json.dumps(input_obj, ensure_ascii=False), encoding="utf-8")
    p = subprocess.run(
        ["gh", "api", "graphql", "--input", str(tmp)],
        check=True,
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    data = json.loads(p.stdout)
    if "errors" in data:
        raise RuntimeError(json.dumps(data["errors"], ensure_ascii=False))
    return data


def main() -> int:
    load_token()
    state = gh_api(
        {
            "query": """
            query($id:ID!){
              node(id:$id){
                ... on ProjectV2 {
                  fields(first:30){
                    nodes {
                      ... on ProjectV2SingleSelectField { id name options { id name } }
                    }
                  }
                  items(first:50){
                    nodes {
                      id
                      content { ... on Issue { number title } }
                    }
                  }
                }
              }
            }
            """,
            "variables": {"id": PROJECT_ID},
        }
    )["data"]["node"]

    status_field = None
    for f in state["fields"]["nodes"]:
        if f and f.get("name") == "Status":
            status_field = f
            break
    if not status_field:
        raise RuntimeError("Status field not found")

    options = {o["name"]: o["id"] for o in status_field["options"]}
    print("Status options:", options)
    in_progress = options.get("In Progress") or options.get("in progress")
    if not in_progress:
        # fallback: any option containing Progress
        for name, oid in options.items():
            if "Progress" in name or "进行" in name:
                in_progress = oid
                print("using status option:", name)
                break
    if not in_progress:
        raise RuntimeError(f"No In Progress option in {options}")

    for item in state["items"]["nodes"]:
        content = item.get("content") or {}
        num = content.get("number")
        if num not in TARGET_NUMBERS:
            continue
        print(f"#{num} -> In Progress item={item['id']}")
        gh_api(
            {
                "query": """
                mutation($projectId:ID!, $itemId:ID!, $fieldId:ID!, $optionId:String!){
                  updateProjectV2ItemFieldValue(input:{
                    projectId:$projectId,
                    itemId:$itemId,
                    fieldId:$fieldId,
                    value:{ singleSelectOptionId:$optionId }
                  }){ projectV2Item { id } }
                }
                """,
                "variables": {
                    "projectId": PROJECT_ID,
                    "itemId": item["id"],
                    "fieldId": status_field["id"],
                    "optionId": in_progress,
                },
            }
        )

    # verify assignees
    for n in sorted(TARGET_NUMBERS):
        issue = json.loads(
            subprocess.check_output(
                ["gh", "api", f"repos/{REPO}/issues/{n}"],
                text=True,
                encoding="utf-8",
            )
        )
        assignees = [a["login"] for a in issue.get("assignees", [])]
        print(f"#{n} {issue['title']} -> {assignees}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
