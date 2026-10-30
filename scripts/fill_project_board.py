#!/usr/bin/env python3
"""Add issues #1-28 to project and create Role/Phase/Priority fields."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "AntonyTang-AT/Multi-agent_Learning_Planning_Assistant"
PROJECT_ID = "PVT_kwHOBU1eIc4BpdPU"
STATUS_FIELD_ID = "PVTSSF_lAHOBU1eIc4BpdPUzhn4z6A"
STATUS_TODO = "f75ad846"


def load_token() -> None:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("GITHUB_TOKEN="):
            os.environ["GH_TOKEN"] = line.split("=", 1)[1].strip()
            return


def gh_api(*args: str, input_obj: dict | None = None) -> dict:
    cmd = ["gh", "api", "graphql"]
    if input_obj is not None:
        tmp = Path(__file__).with_name("_gql_input.json")
        tmp.write_text(json.dumps(input_obj, ensure_ascii=False), encoding="utf-8")
        cmd.extend(["--input", str(tmp)])
    else:
        cmd.extend(args)
    p = subprocess.run(cmd, check=True, text=True, capture_output=True, encoding="utf-8")
    data = json.loads(p.stdout)
    if "errors" in data:
        raise RuntimeError(json.dumps(data["errors"], ensure_ascii=False))
    return data


def main() -> int:
    load_token()

    # Create fields with ASCII-safe GraphQL file
    mutations = [
        (
            "角色",
            [
                {"name": "前端", "color": "BLUE", "description": "frontend"},
                {"name": "后端", "color": "GREEN", "description": "backend"},
                {"name": "Agent", "color": "PURPLE", "description": "agent"},
                {"name": "资料", "color": "YELLOW", "description": "data"},
                {"name": "答辩", "color": "ORANGE", "description": "pitch"},
                {"name": "闸门", "color": "GRAY", "description": "gate"},
            ],
        ),
        (
            "阶段",
            [
                {"name": "12号前", "color": "GREEN", "description": "pre-12"},
                {"name": "12号后", "color": "YELLOW", "description": "post-12"},
                {"name": "闸门", "color": "RED", "description": "gate"},
            ],
        ),
        (
            "优先级",
            [
                {"name": "P0", "color": "RED", "description": "must"},
                {"name": "P1", "color": "ORANGE", "description": "nice"},
            ],
        ),
    ]

    # Check existing fields
    existing = gh_api(
        input_obj={
            "query": """
            query($id:ID!){
              node(id:$id){
                ... on ProjectV2 {
                  fields(first:30){
                    nodes {
                      ... on ProjectV2FieldCommon { id name }
                      ... on ProjectV2SingleSelectField { id name options { id name } }
                    }
                  }
                }
              }
            }
            """,
            "variables": {"id": PROJECT_ID},
        }
    )
    names = {n.get("name") for n in existing["data"]["node"]["fields"]["nodes"] if n.get("name")}
    print("existing fields:", sorted(names))

    for field_name, options in mutations:
        if field_name in names:
            print(f"skip field {field_name}")
            continue
        q = {
            "query": """
            mutation($projectId:ID!, $name:String!, $options:[ProjectV2SingleSelectFieldOptionInput!]!){
              createProjectV2Field(input:{
                projectId:$projectId,
                dataType:SINGLE_SELECT,
                name:$name,
                singleSelectOptions:$options
              }){
                projectV2Field {
                  ... on ProjectV2SingleSelectField { id name options { id name } }
                }
              }
            }
            """,
            "variables": {"projectId": PROJECT_ID, "name": field_name, "options": options},
        }
        out = gh_api(input_obj=q)
        print("created field", field_name, out["data"]["createProjectV2Field"]["projectV2Field"]["id"])

    # Map issue labels -> field options after refresh
    fields = gh_api(
        input_obj={
            "query": """
            query($id:ID!){
              node(id:$id){
                ... on ProjectV2 {
                  fields(first:30){
                    nodes {
                      ... on ProjectV2SingleSelectField { id name options { id name } }
                    }
                  }
                }
              }
            }
            """,
            "variables": {"id": PROJECT_ID},
        }
    )["data"]["node"]["fields"]["nodes"]
    field_map = {}
    for f in fields:
        if not f or "name" not in f:
            continue
        field_map[f["name"]] = {
            "id": f["id"],
            "options": {o["name"]: o["id"] for o in f.get("options", [])},
        }

    role_from_title = {
        "[闸门]": "闸门",
        "[前端]": "前端",
        "[后端]": "后端",
        "[Agent]": "Agent",
        "[资料]": "资料",
        "[答辩]": "答辩",
    }

    for n in range(1, 29):
        issue = json.loads(
            subprocess.check_output(
                [
                    "gh",
                    "api",
                    f"repos/{REPO}/issues/{n}",
                ],
                text=True,
                encoding="utf-8",
            )
        )
        content_id = issue["node_id"]
        title = issue["title"]
        label_names = [x["name"] for x in issue.get("labels", [])]

        add = gh_api(
            input_obj={
                "query": """
                mutation($projectId:ID!, $contentId:ID!){
                  addProjectV2ItemById(input:{projectId:$projectId, contentId:$contentId}){
                    item { id }
                  }
                }
                """,
                "variables": {"projectId": PROJECT_ID, "contentId": content_id},
            }
        )
        item_id = add["data"]["addProjectV2ItemById"]["item"]["id"]
        print(f"#{n} item={item_id}")

        # Status = Todo
        gh_api(
            input_obj={
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
                    "itemId": item_id,
                    "fieldId": STATUS_FIELD_ID,
                    "optionId": STATUS_TODO,
                },
            }
        )

        role = next((v for k, v in role_from_title.items() if title.startswith(k)), None)
        if role and "角色" in field_map and role in field_map["角色"]["options"]:
            gh_api(
                input_obj={
                    "query": """
                    mutation($projectId:ID!, $itemId:ID!, $fieldId:ID!, $optionId:String!){
                      updateProjectV2ItemFieldValue(input:{
                        projectId:$projectId, itemId:$itemId, fieldId:$fieldId,
                        value:{ singleSelectOptionId:$optionId }
                      }){ projectV2Item { id } }
                    }
                    """,
                    "variables": {
                        "projectId": PROJECT_ID,
                        "itemId": item_id,
                        "fieldId": field_map["角色"]["id"],
                        "optionId": field_map["角色"]["options"][role],
                    },
                }
            )

        phase = None
        if "phase:gate" in label_names:
            phase = "闸门"
        elif "phase:post-12" in label_names:
            phase = "12号后"
        elif "phase:pre-12" in label_names:
            phase = "12号前"
        if phase and "阶段" in field_map and phase in field_map["阶段"]["options"]:
            gh_api(
                input_obj={
                    "query": """
                    mutation($projectId:ID!, $itemId:ID!, $fieldId:ID!, $optionId:String!){
                      updateProjectV2ItemFieldValue(input:{
                        projectId:$projectId, itemId:$itemId, fieldId:$fieldId,
                        value:{ singleSelectOptionId:$optionId }
                      }){ projectV2Item { id } }
                    }
                    """,
                    "variables": {
                        "projectId": PROJECT_ID,
                        "itemId": item_id,
                        "fieldId": field_map["阶段"]["id"],
                        "optionId": field_map["阶段"]["options"][phase],
                    },
                }
            )

        pri = "P0" if "priority:P0" in label_names else ("P1" if "priority:P1" in label_names else None)
        if pri and "优先级" in field_map and pri in field_map["优先级"]["options"]:
            gh_api(
                input_obj={
                    "query": """
                    mutation($projectId:ID!, $itemId:ID!, $fieldId:ID!, $optionId:String!){
                      updateProjectV2ItemFieldValue(input:{
                        projectId:$projectId, itemId:$itemId, fieldId:$fieldId,
                        value:{ singleSelectOptionId:$optionId }
                      }){ projectV2Item { id } }
                    }
                    """,
                    "variables": {
                        "projectId": PROJECT_ID,
                        "itemId": item_id,
                        "fieldId": field_map["优先级"]["id"],
                        "optionId": field_map["优先级"]["options"][pri],
                    },
                }
            )

    # final count
    final = gh_api(
        input_obj={
            "query": """
            query($id:ID!){
              node(id:$id){
                ... on ProjectV2 {
                  title url public items { totalCount }
                }
              }
            }
            """,
            "variables": {"id": PROJECT_ID},
        }
    )
    print(json.dumps(final["data"]["node"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
