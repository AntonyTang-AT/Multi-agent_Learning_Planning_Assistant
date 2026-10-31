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

# 词表：与 data/README.md 的「双场景标签规范」保持一致
SCENARIO_TAGS = {"final_review", "catch_up"}
DIFFICULTY_RANGE = (1, 5)


def check_outline(path: Path) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    if "nodes" not in data:
        errors.append(f"{path.name}: missing nodes")
        return errors

    nodes = data["nodes"]
    ids: list[str] = []
    for node in nodes:
        if "id" not in node or "name" not in node:
            errors.append(f"{path.name}: node missing id/name")
            continue
        ids.append(node["id"])

    dup = {i for i in ids if ids.count(i) > 1}
    for d in sorted(dup):
        errors.append(f"{path.name}: duplicate id {d}")

    known = set(ids)
    for node in nodes:
        nid = node.get("id")
        for child in node.get("children", []) or []:
            if child not in known:
                errors.append(f"{path.name}:{nid}: child '{child}' not defined")
        for pre in node.get("prerequisites", []) or []:
            if pre not in known:
                errors.append(f"{path.name}:{nid}: prerequisite '{pre}' not defined")
            if pre == nid:
                errors.append(f"{path.name}:{nid}: prerequisite cannot be itself")
        parent = node.get("parent")
        if parent and parent not in known:
            errors.append(f"{path.name}:{nid}: parent '{parent}' not defined")

    # 章节点声明的 children，其 parent 必须指回本章
    by_id = {n["id"]: n for n in nodes if "id" in n}
    for node in nodes:
        for child in node.get("children", []) or []:
            cn = by_id.get(child)
            if cn is not None and cn.get("parent") != node.get("id"):
                errors.append(
                    f"{path.name}:{node.get('id')}: child '{child}' 的 parent 未指回本章"
                )
    return errors


def check_questions(path: Path, known_ids: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    for q in data.get("questions", []):
        qid = q.get("question_id")
        missing = REQUIRED_QUESTION_FIELDS - set(q)
        if missing:
            errors.append(f"{path.name}:{qid}: missing {sorted(missing)}")
            continue
        bad = set(q.get("scenario_tags") or []) - SCENARIO_TAGS
        if bad:
            errors.append(f"{path.name}:{qid}: 非法 scenario_tags {sorted(bad)}")
        diff = q.get("difficulty")
        if not isinstance(diff, int) or not DIFFICULTY_RANGE[0] <= diff <= DIFFICULTY_RANGE[1]:
            errors.append(f"{path.name}:{qid}: difficulty 必须是 {DIFFICULTY_RANGE[0]}-{DIFFICULTY_RANGE[1]} 整数")
        kids = q.get("knowledge_ids") or []
        if not kids:
            errors.append(f"{path.name}:{qid}: knowledge_ids 不能为空")
        elif known_ids:
            unk = [k for k in kids if k not in known_ids]
            if unk:
                errors.append(f"{path.name}:{qid}: knowledge_ids 不在 taxonomy 中 {unk}")
    return errors


# ---------------- v1.0 新增：materials / exams / 场景聚合 ----------------

MATERIAL_KINDS = {"textbook", "courseware", "homework", "answer_book", "textbook_reference"}
EXAM_KINDS = {"paper", "answer", "paper_photo", "paper_doc"}


def check_materials(path: Path, known_ids: set[str]) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    seen: set[str] = set()
    for it in data.get("items", []):
        mid = it.get("material_id")
        if not mid:
            errors.append(f"{path.name}: 存在缺 material_id 的条目")
            continue
        if mid in seen:
            errors.append(f"{path.name}:{mid}: material_id 重复")
        seen.add(mid)
        cid = it.get("chapter_id")
        if cid and cid not in known_ids:
            errors.append(f"{path.name}:{mid}: chapter_id '{cid}' 不在 taxonomy 中")
        if it.get("kind") not in MATERIAL_KINDS:
            errors.append(f"{path.name}:{mid}: 非法 kind '{it.get('kind')}'")
        if not it.get("file"):
            errors.append(f"{path.name}:{mid}: file 不能为空")
        if not it.get("license_note"):
            errors.append(f"{path.name}:{mid}: 缺 license_note")
    return errors


def check_exams(path: Path) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    seen: set[str] = set()
    for it in data.get("items", []):
        eid = it.get("exam_id")
        if not eid:
            errors.append(f"{path.name}: 存在缺 exam_id 的条目")
            continue
        if eid in seen:
            errors.append(f"{path.name}:{eid}: exam_id 重复")
        seen.add(eid)
        if it.get("kind") not in EXAM_KINDS:
            errors.append(f"{path.name}:{eid}: 非法 kind '{it.get('kind')}'")
        if not it.get("file"):
            errors.append(f"{path.name}:{eid}: file 不能为空")
    return errors


def check_exam_hot(path: Path, known_ids: set[str]) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    for key, val in (data.get("items") or {}).items():
        if key not in known_ids:
            errors.append(f"{path.name}:{key}: 不在 taxonomy 中")
        hot = val.get("exam_hot")
        if not isinstance(hot, bool):
            errors.append(f"{path.name}:{key}: exam_hot 必须是布尔")
        elif hot and val.get("years_hit", 0) < 2:
            errors.append(f"{path.name}:{key}: exam_hot=true 但 years_hit<2，违反判定规则")
    return errors


def check_scene(path: Path, known_ids: set[str], question_ids: set[str],
                chapter_ids: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    for ch in data.get("chapters", []):
        cid = ch.get("chapter_id")
        if cid not in known_ids:
            errors.append(f"{path.name}:{cid}: 章不在 taxonomy 中")
        elif chapter_ids is not None and cid not in chapter_ids:
            # 知识点被当成章用会让「N 章」的统计虚高（曾出现 20 章）
            errors.append(f"{path.name}:{cid}: chapter_id 必须是章级节点，不能是知识点")
        seen: set[str] = set()
        for q in ch.get("questions", []):
            qid = q.get("question_id")
            if qid not in question_ids:
                errors.append(f"{path.name}:{cid}: 引用了不存在的题 {qid}")
            if qid in seen:
                errors.append(f"{path.name}:{cid}: 题 {qid} 重复")
            seen.add(qid)
        if ch.get("question_count") != len(ch.get("questions", [])):
            errors.append(f"{path.name}:{cid}: question_count 与实际条目数不一致")
    return errors


def _outline_files() -> list[Path]:
    """仅大纲文件；跳过 aliases.json 等非 outline 合同文件。"""
    return sorted((ROOT / "taxonomy").glob("*_outline.json"))


def collect_outline_ids() -> set[str]:
    ids: set[str] = set()
    for p in _outline_files():
        data = json.loads(p.read_text(encoding="utf-8"))
        ids.update(n["id"] for n in data.get("nodes", []) if "id" in n)
    return ids


def collect_chapter_ids() -> set[str]:
    """只取章级节点。场景聚合的 chapter_id 必须是章，不能是知识点。"""
    ids: set[str] = set()
    for p in _outline_files():
        data = json.loads(p.read_text(encoding="utf-8"))
        ids.update(n["id"] for n in data.get("nodes", [])
                   if n.get("level") == "chapter" and "id" in n)
    return ids


def main() -> int:
    errors: list[str] = []
    for p in _outline_files():
        errors.extend(check_outline(p))
    known = collect_outline_ids()
    chapters = collect_chapter_ids()
    qids: set[str] = set()
    for p in (ROOT / "questions").glob("*.json"):
        errors.extend(check_questions(p, known))
        qids.update(q.get("question_id") for q in
                    json.loads(p.read_text(encoding="utf-8")).get("questions", [])
                    if q.get("question_id"))

    if (ROOT / "materials" / "index.json").exists():
        errors.extend(check_materials(ROOT / "materials" / "index.json", known))
    if (ROOT / "exams" / "index.json").exists():
        errors.extend(check_exams(ROOT / "exams" / "index.json"))
    for p in (ROOT / "exams").glob("exam_hot_*.json"):
        errors.extend(check_exam_hot(p, known))
    for sub in ("catch_up", "final_review"):
        f = ROOT / sub / "index.json"
        if f.exists():
            errors.extend(check_scene(f, known, qids, chapters))

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
