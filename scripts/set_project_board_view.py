#!/usr/bin/env python3
"""Ensure GitHub Project has a Board layout view (and switch default if needed)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "PVT_kwHOBU1eIc4BpdPU"


def load_token() -> None:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("GITHUB_TOKEN="):
            os.environ["GH_TOKEN"] = line.split("=", 1)[1].strip()
            os.environ.pop("GITHUB_TOKEN", None)
            return


def gql(obj: dict) -> dict:
    tmp = Path(__file__).with_name("_gql_input.json")
    tmp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    p = subprocess.run(
        ["gh", "api", "graphql", "--input", str(tmp)],
        check=False,
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    if p.returncode != 0:
        raise RuntimeError(p.stderr or p.stdout)
    data = json.loads(p.stdout)
    if "errors" in data:
        raise RuntimeError(json.dumps(data["errors"], ensure_ascii=False, indent=2))
    return data


def get_project() -> dict:
    return gql(
        {
            "query": """
            query($id: ID!) {
              node(id: $id) {
                ... on ProjectV2 {
                  title
                  url
                  number
                  views(first: 20) {
                    nodes {
                      id
                      name
                      layout
                      number
                      filter
                    }
                  }
                  fields(first: 30) {
                    nodes {
                      ... on ProjectV2FieldCommon { id name dataType }
                      ... on ProjectV2SingleSelectField {
                        id name dataType
                        options { id name }
                      }
                    }
                  }
                }
              }
            }
            """,
            "variables": {"id": PROJECT_ID},
        }
    )["data"]["node"]


def create_board_view(name: str = "Board") -> dict:
    return gql(
        {
            "query": """
            mutation($projectId: ID!, $name: String!, $layout: ProjectV2ViewLayout!) {
              createProjectV2View(input: {
                projectId: $projectId
                name: $name
                layout: $layout
              }) {
                projectV2View {
                  id
                  name
                  layout
                  number
                }
              }
            }
            """,
            "variables": {
                "projectId": PROJECT_ID,
                "name": name,
                "layout": "BOARD_LAYOUT",
            },
        }
    )["data"]["createProjectV2View"]["projectV2View"]


def update_view_layout(view_id: str, layout: str = "BOARD_LAYOUT") -> dict:
    return gql(
        {
            "query": """
            mutation($viewId: ID!, $layout: ProjectV2ViewLayout!) {
              updateProjectV2View(input: {
                viewId: $viewId
                layout: $layout
              }) {
                projectV2View {
                  id
                  name
                  layout
                  number
                }
              }
            }
            """,
            "variables": {"viewId": view_id, "layout": layout},
        }
    )["data"]["updateProjectV2View"]["projectV2View"]


def rename_view(view_id: str, name: str) -> dict:
    return gql(
        {
            "query": """
            mutation($viewId: ID!, $name: String!) {
              updateProjectV2View(input: {
                viewId: $viewId
                name: $name
              }) {
                projectV2View {
                  id
                  name
                  layout
                  number
                }
              }
            }
            """,
            "variables": {"viewId": view_id, "name": name},
        }
    )["data"]["updateProjectV2View"]["projectV2View"]


def main() -> int:
    load_token()
    proj = get_project()
    print("Project:", proj["title"], proj["url"])
    views = [v for v in proj["views"]["nodes"] if v]
    print("Current views:")
    for v in views:
        print(f"  #{v['number']} {v['name']} layout={v['layout']} id={v['id']}")

    status_field_id = None
    for f in proj["fields"]["nodes"]:
        if f and f.get("name") == "Status":
            status_field_id = f["id"]
            break

    board_views = [v for v in views if v.get("layout") == "BOARD_LAYOUT"]
    if board_views:
        target = board_views[0]
        print("Already has Board view:", target["name"], target["id"])
    else:
        # Prefer converting the first view if it's a table named like default
        if views:
            first = views[0]
            print(f"Converting view '{first['name']}' -> BOARD_LAYOUT")
            try:
                target = update_view_layout(first["id"], "BOARD_LAYOUT")
            except Exception as e:
                print("update layout failed, creating new Board view:", e)
                target = create_board_view("Board")
        else:
            target = create_board_view("Board")
        print("Board view ready:", target)

    # Rename for clarity
    if target.get("name") != "Board":
        target = rename_view(target["id"], "Board")
        print("Renamed view to Board")

    if not status_field_id:
        print("Status field not found; board may use default grouping")
    else:
        print("Status field present; Board layout columns use Status by default in UI")

    final = get_project()
    print("\nFinal views:")
    for v in final["views"]["nodes"]:
        if v:
            print(f"  #{v['number']} {v['name']} layout={v['layout']}")
    print("\nOpen:", final["url"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
