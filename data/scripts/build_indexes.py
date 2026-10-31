#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 exams/index.json（真题台账）与 catch_up/ final_review/ 场景聚合。

- exams/index.json：扫 source 下的真题文件，登记年份/类型/是否有文字层/抽文本结果
- catch_up/index.json：按章聚合（原设计按周次，因缺教务进度表改为按章，见 README §2.4）
- final_review/index.json：按章聚合 + exam_hot 优先排序

用法：python data/scripts/build_indexes.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent.parent / "source"
EXAM_BOOK = [
    ("physics", SRC / "_原始下载" / "大物" / "04_真题", SRC / "_extracted" / "大物真题"),
    ("math", SRC / "_原始下载" / "高数" / "03_真题", SRC / "_extracted" / "高数真题"),
]


def year_of(name: str) -> str | None:
    m = re.search(r"(\d{2})级", name)
    if m:
        return "20" + m.group(1)
    m = re.search(r"(20\d{2})", name)
    return m.group(1) if m else None


def kind_of(name: str) -> str:
    if any(k in name for k in ("答案", "参考", "解答")):
        return "answer"
    if name.lower().endswith((".jpg", ".png", ".doc", ".docx")):
        return "paper_photo" if name.lower().endswith((".jpg", ".png")) else "paper_doc"
    return "paper"


def build_exams() -> dict:
    items = []
    for subject, raw, ext in EXAM_BOOK:
        texts = {}
        if ext.exists():
            for t in ext.rglob("*.txt"):
                blob = t.read_bytes()
                for enc in ("utf-8", "gbk", "latin-1"):
                    try:
                        texts[t.stem] = len(blob.decode(enc))
                        break
                    except UnicodeDecodeError:
                        continue
                texts.setdefault(t.stem, 0)
        for f in sorted(raw.rglob("*")):
            if not f.is_file() or f.suffix.lower() not in (".pdf", ".doc", ".docx", ".jpg", ".png"):
                continue
            stem = f.stem
            n = texts.get(stem, 0)
            items.append({
                "exam_id": f"exam_{subject}_{year_of(f.name) or 'unknown'}_{len(items):03d}",
                "subject": subject,
                "year": year_of(f.name),
                "kind": kind_of(f.name),
                "file": str(f.relative_to(SRC)).replace("\\", "/"),
                "text_extracted": n >= 800,
                "text_chars": n,
                "note": None if n >= 800 else "无文字层（扫描件/照片）或未抽取",
            })
    return {
        "version": "1.0",
        "scope": "大物 A1 期末 2012–2023（48 份）+ 高数 A1 期末 16–24 级（9 份）",
        "rule": "只登记台账与是否可抽文字，不转载题目正文；题面引用以 exams 目录原件为准",
        "counts": {
            "total": len(items),
            "text_extracted": sum(1 for i in items if i["text_extracted"]),
            "by_subject": {s: sum(1 for i in items if i["subject"] == s) for s in ("math", "physics")},
        },
        "items": items,
    }


def build_scenes() -> tuple[dict, dict]:
    taxo = {}
    parent_of: dict[str, str] = {}
    for key in ("math", "physics"):
        data = json.loads((ROOT / "taxonomy" / f"{key}_outline.json").read_text(encoding="utf-8"))
        for n in data["nodes"]:
            if n["level"] == "chapter":
                taxo[n["id"]] = n
            elif n.get("parent"):
                parent_of[n["id"]] = n["parent"]

    questions = []
    for p in sorted((ROOT / "questions").glob("*.json")):
        questions.extend(json.loads(p.read_text(encoding="utf-8")).get("questions", []))

    def scene(tag: str) -> dict:
        buckets: dict[str, list[dict]] = {}
        for q in questions:
            if tag not in (q.get("scenario_tags") or []):
                continue
            for kid in q["knowledge_ids"]:
                # 知识点要归到父章节；直接当章节用会让统计出 20 章这种假数据
                ch = kid if kid in taxo else parent_of.get(kid, kid)
                if ch not in taxo:
                    raise SystemExit(f"[!] {q['question_id']} 的 knowledge_id '{kid}' 找不到所属章节")
                buckets.setdefault(ch, []).append({
                    "question_id": q["question_id"],
                    "difficulty": q["difficulty"],
                    "type": q["type"],
                    "exam_hot": bool(q.get("exam_hot")),
                })
        chapters = []
        for cid, qs in buckets.items():
            node = taxo.get(cid, {})
            qs.sort(key=lambda x: (-x["exam_hot"], -x["difficulty"], x["question_id"]))
            chapters.append({
                "chapter_id": cid,
                "no": node.get("no"),
                "name": node.get("name"),
                "question_count": len(qs),
                "hot_count": sum(1 for x in qs if x["exam_hot"]),
                "questions": qs,
            })
        chapters.sort(key=lambda c: (c["no"] or 99))
        return {
            "scenario": tag,
            "version": "1.0",
            "aggregate_by": "chapter",
            "note": "按章聚合（原按周次，因缺教务进度表改按章，见 data/README.md §2.4）"
                    if tag == "catch_up" else "按章聚合，章内按 exam_hot → difficulty 排序",
            "counts": {"chapters": len(chapters),
                       "questions": sum(c["question_count"] for c in chapters)},
            "chapters": chapters,
        }

    return scene("catch_up"), scene("final_review")


def main() -> int:
    ex = build_exams()
    (ROOT / "exams" / "index.json").write_text(
        json.dumps(ex, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[exams] {ex['counts']}")

    cu, fr = build_scenes()
    for name, doc in (("catch_up", cu), ("final_review", fr)):
        d = ROOT / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[{name}] {doc['counts']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
