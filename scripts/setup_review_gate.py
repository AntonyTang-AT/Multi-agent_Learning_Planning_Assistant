#!/usr/bin/env python3
"""Add Project Status「审核中」+ protect main so others need owner review."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "AntonyTang-AT/Multi-agent_Learning_Planning_Assistant"
PROJECT_ID = "PVT_kwHOBU1eIc4BpdPU"
OWNER_LOGIN = "AntonyTang-AT"
STATUS_OPTION_NAME = "审核中"


def load_token() -> None:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("GITHUB_TOKEN="):
            os.environ["GH_TOKEN"] = line.split("=", 1)[1].strip()
            os.environ.pop("GITHUB_TOKEN", None)
            return


def run(cmd: list[str], input_text: str | None = None) -> str:
    p = subprocess.run(
        cmd,
        input=input_text,
        check=False,
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    if p.returncode != 0:
        raise RuntimeError(f"cmd failed: {' '.join(cmd)}\n{p.stderr or p.stdout}")
    return p.stdout


def gql(obj: dict) -> dict:
    tmp = Path(__file__).with_name("_gql_input.json")
    tmp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    out = run(["gh", "api", "graphql", "--input", str(tmp)])
    data = json.loads(out)
    if "errors" in data:
        raise RuntimeError(json.dumps(data["errors"], ensure_ascii=False, indent=2))
    return data


def gh_api_json(method: str, path: str, body: dict | None = None) -> dict | list | None:
    cmd = ["gh", "api", "-X", method, path]
    if body is not None:
        tmp = Path(__file__).with_name("_rest_body.json")
        tmp.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
        cmd.extend(["--input", str(tmp)])
    out = run(cmd)
    return json.loads(out) if out.strip() else None


def get_status_field() -> dict:
    data = gql(
        {
            "query": """
            query($id: ID!) {
              node(id: $id) {
                ... on ProjectV2 {
                  fields(first: 30) {
                    nodes {
                      ... on ProjectV2SingleSelectField {
                        id
                        name
                        options { id name color description }
                      }
                    }
                  }
                }
              }
            }
            """,
            "variables": {"id": PROJECT_ID},
        }
    )
    for f in data["data"]["node"]["fields"]["nodes"]:
        if f and f.get("name") == "Status":
            return f
    raise RuntimeError("Status field not found")


def ensure_status_option(field: dict) -> None:
    options = field["options"]
    names = {o["name"] for o in options}
    print("Current Status options:", [o["name"] for o in options])
    if STATUS_OPTION_NAME in names:
        print(f"Status already has「{STATUS_OPTION_NAME}」")
        return

    # Preserve existing options (with id) and append new one.
    # Insert before Done if present, else append.
    color_map = {
        "GRAY": "GRAY",
        "BLUE": "BLUE",
        "GREEN": "GREEN",
        "YELLOW": "YELLOW",
        "ORANGE": "ORANGE",
        "RED": "RED",
        "PINK": "PINK",
        "PURPLE": "PURPLE",
    }
    new_opts: list[dict] = []
    inserted = False
    for o in options:
        if o["name"] == "Done" and not inserted:
            new_opts.append(
                {
                    "name": STATUS_OPTION_NAME,
                    "color": "YELLOW",
                    "description": "PR / 交付待仓库负责人审核",
                }
            )
            inserted = True
        new_opts.append(
            {
                "id": o["id"],
                "name": o["name"],
                "color": color_map.get(o.get("color") or "GRAY", "GRAY"),
                "description": o.get("description") or "",
            }
        )
    if not inserted:
        new_opts.append(
            {
                "name": STATUS_OPTION_NAME,
                "color": "YELLOW",
                "description": "PR / 交付待仓库负责人审核",
            }
        )

    result = gql(
        {
            "query": """
            mutation($fieldId: ID!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
              updateProjectV2Field(input: {
                fieldId: $fieldId
                singleSelectOptions: $options
              }) {
                projectV2Field {
                  ... on ProjectV2SingleSelectField {
                    id
                    name
                    options { id name }
                  }
                }
              }
            }
            """,
            "variables": {"fieldId": field["id"], "options": new_opts},
        }
    )
    updated = result["data"]["updateProjectV2Field"]["projectV2Field"]["options"]
    print("Updated Status options:", [o["name"] for o in updated])


def ensure_codeowners() -> Path:
    path = ROOT / ".github" / "CODEOWNERS"
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "# 默认：所有变更需仓库负责人审核后才能合入 main\n"
        f"* @{OWNER_LOGIN}\n"
    )
    if path.exists() and path.read_text(encoding="utf-8") == content:
        print("CODEOWNERS already up to date")
    else:
        path.write_text(content, encoding="utf-8")
        print(f"Wrote {path.relative_to(ROOT)}")
    return path


def ensure_branch_protection() -> None:
    """Protect main: PR required + code owner review; admin (you) can still bypass."""
    body = {
        "required_status_checks": None,
        "enforce_admins": False,
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": True,
            "required_approving_review_count": 1,
            "require_last_push_approval": False,
        },
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False,
        "block_creations": False,
        "required_conversation_resolution": True,
        "lock_branch": False,
        "allow_fork_syncing": False,
    }
    try:
        result = gh_api_json(
            "PUT",
            f"repos/{REPO}/branches/main/protection",
            body,
        )
        print("Branch protection on main applied")
        reviews = (result or {}).get("required_pull_request_reviews") or {}
        print(
            "  require_code_owner_reviews=",
            reviews.get("require_code_owner_reviews"),
            "approvals=",
            reviews.get("required_approving_review_count"),
        )
    except Exception as e:
        print("Classic branch protection failed, trying ruleset:", e)
        ensure_ruleset()


def ensure_ruleset() -> None:
    existing = gh_api_json("GET", f"repos/{REPO}/rulesets") or []
    name = "main-requires-owner-review"
    for r in existing:
        if r.get("name") == name:
            print(f"Ruleset already exists: id={r.get('id')}")
            return

    body = {
        "name": name,
        "target": "branch",
        "enforcement": "active",
        "conditions": {
            "ref_name": {
                "include": ["refs/heads/main"],
                "exclude": [],
            }
        },
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {
                "type": "pull_request",
                "parameters": {
                    "required_approving_review_count": 1,
                    "dismiss_stale_reviews_on_push": True,
                    "require_code_owner_review": True,
                    "require_last_push_approval": False,
                    "required_review_thread_resolution": True,
                },
            },
        ],
        "bypass_actors": [
            {
                "actor_id": 5,  # RepositoryRole admin — often works for owner bypass
                "actor_type": "RepositoryRole",
                "bypass_mode": "always",
            }
        ],
    }
    try:
        created = gh_api_json("POST", f"repos/{REPO}/rulesets", body)
        print("Created ruleset:", (created or {}).get("id"), (created or {}).get("name"))
    except Exception as e:
        # retry without bypass_actors if role id invalid
        print("Ruleset with bypass failed:", e)
        body.pop("bypass_actors", None)
        created = gh_api_json("POST", f"repos/{REPO}/rulesets", body)
        print("Created ruleset (no bypass):", (created or {}).get("id"))


def main() -> int:
    load_token()
    field = get_status_field()
    ensure_status_option(field)
    ensure_codeowners()
    ensure_branch_protection()

    # Verify protection
    try:
        prot = gh_api_json("GET", f"repos/{REPO}/branches/main/protection")
        print("\nVerified protection URL keys:", list((prot or {}).keys())[:8])
    except Exception as e:
        print("Verify protection:", e)
        rules = gh_api_json("GET", f"repos/{REPO}/rulesets")
        print("Rulesets:", rules)

    print(
        "\nDone.\n"
        f"- Board: https://github.com/users/{OWNER_LOGIN}/projects/4\n"
        f"- Settings: https://github.com/{REPO}/settings/branches\n"
        "Workflow: 他人开 PR → 看板可标「审核中」→ 你 Approve 后才能合入 main。\n"
        "你本人作为 admin 仍可直接推 main（enforce_admins=false）。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
