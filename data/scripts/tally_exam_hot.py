#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从已抽取的真题正文统计考点频次 → exams/exam_hot_<subject>.json

口径（写进输出文件，可复核）：
- 按年份去重：某考点在 N 个年份的正文里出现过 → years_hit = N
- exam_hot = years_hit >= 2（对齐 data/README.md §2.2 的判定规则）
- 无法参与统计的年份（扫描件无文字层 / 仅 .doc）显式列出，不参与计算，也不冒充「没考」

两门课底本不同，必须如实标注：
- 大物：**试卷正文**（2012–2019、2022 共 8 年可抽文字），知识点级关键词
- 高数：试卷是扫描件，只有**参考答案**可抽文字（17/18/19/20/23 共 5 年），故降级到**章级**，
  且答案会省略题干术语，命中率偏低

用法：python data/scripts/tally_exam_hot.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT.parent.parent / "source" / "_extracted"

PHY_KEYWORDS: dict[str, list[str]] = {
    "phy.kinematics.kp01": ["参考系", "质点模型"],
    "phy.kinematics.kp02": ["位矢", "位移", "瞬时速度"],
    "phy.kinematics.kp03": ["法向加速度", "切向加速度", "曲率半径"],
    "phy.kinematics.kp04": ["角速度", "角加速度", "相对运动"],
    "phy.dynamics.kp01": ["牛顿第二定律", "牛顿定律", "受力分析"],
    "phy.dynamics.kp02": ["动量守恒", "动量定理", "冲量"],
    "phy.dynamics.kp03": ["动能定理", "变力作功", "功率"],
    "phy.dynamics.kp04": ["机械能守恒", "势能", "功能原理", "保守力"],
    "phy.dynamics.kp05": ["角动量", "动量矩"],
    "phy.rigid.kp01": ["转动惯量", "转动定律", "力矩"],
    "phy.rigid.kp02": ["转动动能", "刚体的机械能", "刚体定轴"],
    "phy.rigid.kp03": ["角动量守恒"],
    "phy.vibration.kp01": ["简谐振动", "振幅", "初相"],
    "phy.vibration.kp02": ["旋转矢量"],
    "phy.vibration.kp03": ["振动能量", "谐振动能量"],
    "phy.vibration.kp04": ["振动合成", "合振动"],
    "phy.wave.kp01": ["波函数", "简谐波", "波动方程"],
    "phy.wave.kp02": ["波的能量", "能量密度", "能流密度"],
    "phy.wave.kp03": ["相干", "相位差", "波程差"],
    "phy.wave.kp04": ["驻波", "波节", "波腹"],
    "phy.wave.kp05": ["多普勒"],
    "phy.interference.kp01": ["双缝", "杨氏"],
    "phy.interference.kp02": ["光程", "劈尖", "牛顿环", "增透", "等厚"],
    "phy.interference.kp03": ["迈克耳逊", "等倾"],
    "phy.diffraction.kp01": ["单缝", "半波带", "夫琅禾费"],
    "phy.diffraction.kp02": ["光栅", "缺级"],
    "phy.diffraction.kp03": ["分辨", "圆孔", "瑞利", "X射线"],
    "phy.polarization.kp01": ["偏振片", "马吕斯", "起偏"],
    "phy.polarization.kp02": ["布儒斯特", "反射光"],
    "phy.polarization.kp03": ["双折射", "o光", "e光", "光轴"],
    "phy.kinetic.kp01": ["状态方程", "平衡态"],
    "phy.kinetic.kp02": ["自由度", "内能", "均分"],
    "phy.kinetic.kp03": ["速率分布", "最概然", "方均根"],
    "phy.kinetic.kp04": ["平均自由程", "碰撞频率"],
    "phy.thermo.kp01": ["热力学第一定律", "准静态"],
    "phy.thermo.kp02": ["等温", "等压", "等容", "绝热", "摩尔热容"],
    "phy.thermo.kp03": ["循环效率", "卡诺", "循环过程"],
    "phy.thermo.kp04": ["热力学第二定律", "熵", "可逆"],
}

MATH_KEYWORDS: dict[str, list[str]] = {
    "math.a1.ch01": ["定义域", "反函数", "复合函数", "奇偶", "有界"],
    "math.a1.ch02": ["极限", "无穷小", "等价无穷小", "数列"],
    "math.a1.ch03": ["连续", "间断点", "零点定理", "介值"],
    "math.a1.ch04": ["导数", "微分", "洛必达", "中值定理", "罗尔", "拉格朗日", "柯西"],
    "math.a1.ch05": ["单调", "极值", "最值", "凹凸", "拐点", "渐近线", "曲率"],
    "math.a1.ch06": ["不定积分", "定积分", "原函数", "换元", "分部积分", "反常积分"],
    "math.a1.ch07": ["面积", "弧长", "旋转体", "体积", "微元"],
    "math.a1.ch08": ["微分方程", "通解", "特解", "特征方程", "齐次"],
}

JOBS = [
    {
        "subject": "physics",
        "src": SRC_ROOT / "大物真题",
        "keywords": PHY_KEYWORDS,
        "level": "knowledge_point",
        "basis": "试卷正文（文件名含「答案/参考/解答」的排除）",
        "excluded_years": {
            "2017": "2017期末.pdf 无文字层（PDF 内为图片帧）",
            "2020": "2020 试卷为扫描件，无文字层",
            "2021": "2021 春试卷为扫描件（另有 4 张 jpg 照片）",
            "2023": "2023 仅 .doc 一份（含答案），非试卷正文，未计入",
        },
        "caveat": "关键词法会漏掉纯公式题：exam_hot=true 可作高频依据，exam_hot=false 不等于没考过",
    },
    {
        "subject": "math",
        "src": SRC_ROOT / "高数真题",
        "keywords": MATH_KEYWORDS,
        "level": "chapter",
        "basis": "参考答案正文（试卷本体为扫描件，无文字层）",
        "excluded_years": {
            "2016": "16 级参考答案为扫描件",
            "2021": "21 级参考答案含图片帧",
            "2022": "22 级参考答案为扫描件",
            "2024": "24 级为合并扫描件",
        },
        "caveat": "底本是答案不是试卷，答案常省略题干术语，故统计降级到章级；exam_hot=false 不可解读为没考",
    },
]


def year_of(name: str) -> str | None:
    m = re.search(r"(\d{2})级", name)
    if m:
        return "20" + m.group(1)
    m = re.search(r"(20\d{2})", name)
    return m.group(1) if m else None


def run(job: dict) -> dict:
    src: Path = job["src"]
    papers: dict[str, str] = {}
    pattern = "**/*.txt" if job["subject"] == "physics" else "*.txt"
    for f in sorted(src.glob(pattern)):
        if job["subject"] == "physics" and any(k in f.name for k in ("答案", "参考", "解答")):
            continue
        y = year_of(f.name)
        txt = f.read_text(encoding="utf-8")
        if not y or len(txt) < 800:
            continue
        papers[y] = papers.get(y, "") + txt

    covered = sorted(papers)
    stats = {}
    for key, kws in job["keywords"].items():
        per_year = {y: sum(papers[y].count(k) for k in kws) for y in covered}
        hit = [y for y, c in per_year.items() if c > 0]
        stats[key] = {
            "hits_per_year": per_year,
            "years_hit": len(hit),
            "hit_years": hit,
            "exam_hot": len(hit) >= 2,
        }
    return {
        "subject": job["subject"],
        "version": "1.0",
        "level": job["level"],
        "method": "关键词命中统计（data/scripts/tally_exam_hot.py，可复跑复核）",
        "rule": "某考点在 >=2 个年份的正文中出现 → exam_hot = true（对齐 data/README.md §2.2）",
        "basis": job["basis"],
        "source": str(src.relative_to(ROOT.parent.parent)).replace("\\", "/"),
        "covered_years": covered,
        "excluded_years": job["excluded_years"],
        "caveat": job["caveat"],
        "counts": {
            "covered_years": len(covered),
            "items": len(stats),
            "hot": sum(1 for v in stats.values() if v["exam_hot"]),
        },
        "items": stats,
    }


def main() -> int:
    for job in JOBS:
        doc = run(job)
        out = ROOT / "exams" / f"exam_hot_{job['subject']}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[{job['subject']}] 覆盖 {doc['covered_years']} | 高频 "
              f"{doc['counts']['hot']}/{doc['counts']['items']} -> {out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
