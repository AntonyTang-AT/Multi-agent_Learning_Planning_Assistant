#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 materials/index.json：18 章 × 教材/课件/习题册 的元数据台账。

只登记**元数据与页码定位**，不转载正文（对齐 data/README.md §五 版权口径）。
文件路径按 source/_原始下载 下的真实文件名 glob 解析，解析不到直接报错，不允许写猜测路径。
"""
from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent.parent / "source" / "_原始下载"
OUT = ROOT / "materials" / "index.json"

MATH_TB = "高数/00_教材/HNU大学数学1 第3版.pdf"
PHY_TB = "大物/01_教材/大物1新版教材.pdf"

# 章节 -> (课件 glob, 习题册 glob)
MATH = {
    1: ("高数/01_课件/*第1章*.pptx", "高数/02_习题册/综合题一 *集合与函数*.pdf"),
    2: ("高数/01_课件/*第2章*.pptx", "高数/02_习题册/综合题二 *极限*.pdf"),
    3: ("高数/01_课件/*第3章*.pptx", "高数/02_习题册/综合题三 *函数的连续性*.pdf"),
    4: ("高数/01_课件/*第4章*.pptx", "高数/02_习题册/综合题四 *函数的导数与微分*.pdf"),
    5: ("高数/01_课件/*第5章*.pptx", "高数/02_习题册/综合题五 *导数与微分的应用举例*.pdf"),
    6: ("高数/01_课件/*第6章*.pptx", "高数/02_习题册/综合题六 *函数的积分*.pdf"),
    7: ("高数/01_课件/*第7章*.pptx", "高数/02_习题册/综合题七 *定积分的应用举例*.pdf"),
    8: ("高数/01_课件/*第9章*.pptx", "高数/02_习题册/综合题八 *常微分方程*.pdf"),
}
PHY = {
    1: ("大物/02_课件/运动学.pdf", "大物/03_习题册/1章运动学*.docx"),
    2: ("大物/02_课件/质点力学.pdf", "大物/03_习题册/2章质点动力学*.docx"),
    3: ("大物/02_课件/刚体.pdf", "大物/03_习题册/3章刚体*.docx"),
    4: ("大物/02_课件/振动.pdf", "大物/03_习题册/4章 振动*.docx"),
    5: ("大物/02_课件/波动.pdf", "大物/03_习题册/5章 波动*.docx"),
    6: ("大物/02_课件/干涉.pdf", "大物/03_习题册/6章光的干涉*.docx"),
    7: ("大物/02_课件/衍射.pdf", "大物/03_习题册/7章光的衍射*.docx"),
    8: ("大物/02_课件/光的偏振.pdf", "大物/03_习题册/8章光的偏振*.docx"),
    9: ("大物/02_课件/微观热学.pdf", "大物/03_习题册/9章 气体分子运动论*.docx"),
    10: ("大物/02_课件/宏观热学.pdf", "大物/03_习题册/10热力学基本原理*.doc"),
}

# 课件章号与教材不一致的两处，必须在元数据里写明
CW_NOTE = {8: "课件为第二版编号「第9章 常微分方程」，对应第三版 ch8"}

EXTRA = [
    ("math", "math.a1.ch01", "answer_book", "高等数学（上）习题册答案",
     "高数/02_习题册/高等数学（上）习题册答案.pdf",
     "全册习题答案，用于扩题与自测；按章定位需人工翻"),
    ("math", None, "textbook_reference", "《大学数学 1》第 4 版（易学军 等）",
     "高数/00_教材/大学数学 1 第4版 (易学军 朱郁森 袁朝晖).pdf",
     "版本核对用参考，不作为页码依据（页码依据为第 3 版）"),
    ("physics", None, "answer_book", "大学物理学上册课后答案（陈曙光）",
     "大物/01_教材/大学物理学上册课后答案(陈曙光) 密码为690568392.pdf",
     "教材课后题答案，扩题来源"),
]


def resolve(pattern: str) -> str:
    hits = sorted(glob.glob(os.path.join(SRC, pattern)))
    if len(hits) != 1:
        raise SystemExit(f"[!] 匹配到 {len(hits)} 个文件：{pattern}")
    return os.path.relpath(hits[0], SRC).replace("\\", "/")


def main() -> int:
    taxo = {k: json.loads((ROOT / "taxonomy" / f"{k}_outline.json").read_text(encoding="utf-8"))
            for k in ("math", "physics")}
    chapters = {}
    for subj, data in taxo.items():
        for n in data["nodes"]:
            if n["level"] == "chapter":
                chapters[n["id"]] = n

    items = []
    for subj, table in (("math", MATH), ("physics", PHY)):
        tb = MATH_TB if subj == "math" else PHY_TB
        for no, (cw_pat, hw_pat) in table.items():
            cid = _chapter_id(subj, no, chapters)
            ch = chapters[cid]
            pr = ch.get("page_range")
            items.append({
                "material_id": f"mat_{cid.replace('.', '_')}_textbook",
                "subject": subj,
                "chapter_id": cid,
                "kind": "textbook",
                "title": f"教材 {ch['name']}",
                "file": tb,
                "page_range": pr,
                "page_status": ch.get("page_status"),
                "license_note": "校内教学使用·仅登记元数据与页码，不转载正文",
                "status": "downloaded",
            })
            items.append({
                "material_id": f"mat_{cid.replace('.', '_')}_courseware",
                "subject": subj,
                "chapter_id": cid,
                "kind": "courseware",
                "title": f"课件 {ch['name']}",
                "file": resolve(cw_pat),
                "page_range": None,
                "license_note": "校内教学使用·仅登记元数据，不转载正文",
                "status": "downloaded",
                "note": CW_NOTE.get(no) if subj == "math" else None,
            })
            items.append({
                "material_id": f"mat_{cid.replace('.', '_')}_homework",
                "subject": subj,
                "chapter_id": cid,
                "kind": "homework",
                "title": f"习题册 {ch['name']}（含解答）",
                "file": resolve(hw_pat),
                "page_range": None,
                "license_note": "校内教学使用·仅登记元数据，不转载正文",
                "status": "downloaded",
            })

    for subj, cid, kind, title, path, note in EXTRA:
        items.append({
            "material_id": "mat_" + (cid.replace(".", "_") if cid else f"{subj}_general") + "_" + kind,
            "subject": subj,
            "chapter_id": cid,
            "kind": kind,
            "title": title,
            "file": resolve(path),
            "page_range": None,
            "license_note": "校内教学使用·仅登记元数据，不转载正文",
            "status": "downloaded",
            "note": note,
        })

    doc = {
        "version": "1.0",
        "scope": "大学数学 1（上册 8 章）+ 大物 1（第 1–10 章）",
        "rule": "只登记元数据与页码定位，不转载正文；路径相对 source/_原始下载/",
        "counts": {
            "items": len(items),
            "chapters": len(chapters),
            "by_kind": {k: sum(1 for i in items if i["kind"] == k)
                        for k in ("textbook", "courseware", "homework",
                                  "answer_book", "textbook_reference")},
        },
        "items": items,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[ok] {len(items)} 条 -> {OUT}  {doc['counts']['by_kind']}")
    return 0


def _phy_key(no: int) -> str:
    return {1: "kinematics", 2: "dynamics", 3: "rigid", 4: "vibration", 5: "wave",
            6: "interference", 7: "diffraction", 8: "polarization",
            9: "kinetic", 10: "thermo"}[no]


def _chapter_id(subj: str, no: int, chapters: dict) -> str:
    if subj == "math":
        for k in chapters:
            if k.startswith("math.a1.ch") and int(k[-2:]) == no:
                return k
    else:
        return f"phy.{_phy_key(no)}"
    raise SystemExit("章节定位失败")


if __name__ == "__main__":
    sys.exit(main())
