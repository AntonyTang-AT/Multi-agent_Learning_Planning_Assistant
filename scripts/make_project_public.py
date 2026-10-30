import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    if line.startswith("GITHUB_TOKEN="):
        os.environ["GH_TOKEN"] = line.split("=", 1)[1].strip()
        break

payload = {
    "query": (
        "mutation($projectId:ID!){"
        " updateProjectV2(input:{projectId:$projectId, public:true})"
        "{ projectV2 { title url public } } }"
    ),
    "variables": {"projectId": "PVT_kwHOBU1eIc4BpdPU"},
}
tmp = Path(__file__).with_name("_make_public.json")
tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
out = subprocess.check_output(["gh", "api", "graphql", "--input", str(tmp)], text=True, encoding="utf-8")
print(out)
