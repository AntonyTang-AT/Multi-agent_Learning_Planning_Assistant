# data（4 号）

**大学数学 1 + 大学物理 1** 资料包（18 章 / 78 知识点）。服务场景：`final_review`（期末复习）、`catch_up`（跟课补漏）。

> **范围（2026-10-31 收缩，重要）**：只做第 1 学期两门课 —— 高数 **《大学数学 1》第三版上册 8 章**、大物 **《大学物理学（Ⅰ）》1–10 章**。
> **《大学数学 2》下册 7 章**与**大物 A2（电磁学/相对论/量子）**一律不采集、不建题、不写 materials。
> 两个 outline 文件的顶层 `scope` 字段记录了同样的口径；任何跨册题目（如无穷级数、二重积分、静电场）都属越界。

- 职责与验收：`docs/roles/04-资料整理.md`
- 导入方：`backend` 的 import 脚本
- 版权：仅答辩学习使用；摘录与改编范围在此补充；合成数据放 `synthetic/` 并标注

## 目录

| 路径 | 内容 | 生成方式 |
|---|---|---|
| `taxonomy/math_outline.json` · `physics_outline.json` | 大纲与知识点（18 章 / 78 知识点） | 人工核对教材目录页 |
| `intake/collection_list.csv` · `.docx` | **采集清单**：18 章逐章台账（课件/习题册/真题/目标题量/缺口） | `data/intake/build_intake.py` |
| `materials/index.json` | 57 条素材元数据（18 章 × 教材/课件/习题册 + 3 条参考） | `scripts/build_materials.py` |
| `questions/math_sample.json` · `physics_sample.json` | **30 + 15 道样例题**（高数每章 3–4 题，大物每章 1–3 题） | 人工编写，字段对齐 §三 |
| `exams/index.json` | 真题台账（58 份：大物 48 + 高数 10），标是否可抽文字 | `scripts/build_indexes.py` |
| `exams/exam_hot_*.json` | `exam_hot` 统计结果（大物 8 年知识点级 / 高数 5 年章级） | `scripts/tally_exam_hot.py` |
| `catch_up/index.json` · `final_review/index.json` | 场景聚合（按章） | `scripts/build_indexes.py` |
| `scripts/validate_schema.py` | 全量校验（大纲 / 题目 / materials / exams / 场景） | 手写 |

> 三个 `build_*.py` / `tally_*.py` 都是**可复跑**的：改完源数据重跑即可，禁止手改生成物后再回填。

## 导入前检查

```bash
python scripts/validate_schema.py
```

校验范围（`v1.0` 起）：

| 检查项 | 说明 |
|---|---|
| taxonomy 节点 | 必须有 `id` + `name`；`id` 不得重复 |
| `children` | 必须指向**已定义**的节点；被引子节点的 `parent` 必须指回本章 |
| `prerequisites` | 必须指向已定义节点，且不能指向自己 |
| 题目必填字段 | `question_id / subject / knowledge_ids / scenario_tags / difficulty / type / stem / answer / source / license_note` |
| `scenario_tags` | 只能取 `final_review`、`catch_up` |
| `difficulty` | 1–5 的整数 |
| `knowledge_ids` | 非空，且**必须存在于 taxonomy**（防止题挂在不存在的知识点上） |
| `materials` 条目 | `material_id` 唯一、`kind` 在词表内、`chapter_id` 必须在 taxonomy、必须带 `license_note` |
| `exams` 条目 | `exam_id` 唯一、`kind` 在词表内、必须有 `file` |
| `exam_hot` 一致性 | key 必须在 taxonomy；`exam_hot=true` 必须满足 `years_hit≥2`（禁止拍脑袋标高频） |
| 场景聚合 | 引用的 `question_id` 必须存在、章内不重复、`question_count` 与实际条目数一致 |

---

## 一、数据依据与版本

### 教材版本

| 学科 | 教材 | 依据 |
|---|---|---|
| 大学物理 | 《大学物理学（Ⅰ）》，文双春 等，**北京大学出版社，2019.1** | 本校《University Physics Ⅰ》教学大纲（课程代码 **GE03005**）第六节「教材及参考书」；与教材正文页眉「大学物理学（Ⅰ）」一致 |
| 高等数学 | **《大学数学 1》第三版**，湖南大学数学与计量经济学院组编，**高等教育出版社**（上册 PDF p8–p14 目录页原件） | 上册教材目录页原件；**下册《大学数学 2》（2014.3，肖萍等主编）不在本期范围** |

大物参考书（大纲原文）：《大学基础物理学》第3版（张三慧等，清华大学出版社，2010.7）；《普通物理学》第6版（程守洙、江之永等，高等教育出版社，2010.5）。

### 大纲口径

| 文件 | verified | 依据 | 说明 |
|---|---|---|---|
| `taxonomy/physics_outline.json` | ✅ true | 本校教学大纲 GE03005 + 教材目录页 | v2.1：10 章 38 个知识点，每章学时合计 **64**，与大纲一致；`scope.excluded_volume` 列出 A2 七章 |
| `taxonomy/math_outline.json` | ✅ true | 上册教材**目录页原件** | v2.1：**仅上册 8 章 40 个知识点**，章名、节名、页码全部取自目录页，无推断；下册 7 章已从 `nodes` 移除 |

**大物课程范围（重要）**：本大纲是**上册 A1**，只含力学、振动与波动、波动光学、热学。**不含电磁学、相对论、量子力学**（属下册 A2 与后续课程）。任何声称"大物包含电磁学"的题目都会与本大纲冲突。

**高数课程范围（重要）**：本期只做**上册**。第三版把「无穷级数」放在**下册第七章 p311**，因此**无穷级数不是本期考点**——旧资料里"高数上册含级数"（第二版编排）的说法不再成立。

**大纲原件的两处瑕疵**（已按规则处理，勿当成错误数据）：

1. 原件第八章后直接标为「第十章」，缺第九章编号 → 本文件按顺序重编 9、10，原编号保留在 `outline_no` 字段。
2. 原件第八章「学时分配：1」残缺 → 学时按大纲第四节汇总表取 `2 大班 + 1 小班讨论`。

### 教材章号 ≠ 大纲章号（`physics_outline.json` 的 `textbook_map`）

教材 3 篇 10 章，与 64 学时大纲的切分方式不同，**做 materials 引用页码时必须查这张映射**：

| 情况 | 说明 |
|---|---|
| 振动 / 波动 | 教材合成**第 4 章**一章；大纲拆为第 4、5 章 |
| 热学两章 | 教材顺序是 第9章 宏观热力学 → 第10章 微观热力学；大纲顺序相反（分子运动论 → 热力学） |
| **几何光学（教材 第5章 p171）** | **教材有、大纲没有** —— 属自学/选读，不纳入 `final_review` 考点聚合；已单列在 `textbook_only` |

### 页码字段口径

| 字段 | 出现位置 | 含义 |
|---|---|---|
| `page_range: [起, 止]` | 章节点 | 教材正文页码范围；**取不到就给 `null`，不猜** |
| `page_status` | 章节点 | `verified_toc`（目录页核实）/ `partial`（部分缺失） |
| `page_start` | 章节点 | `page_status=partial` 时，唯一已确认的起始页 |
| `page` | 知识点（节）节点 | 该节在教材中的起始页，用于 `materials` 的出处定位 |

> 大物第 1–5 章的 `page_status` 为 `partial`：该 PDF 副本的目录第 1 页是 CMYK 反相扫描，无法读取，第 2–5 章起始页缺失；第 1 章起始页 p3 已由正文页核实。

### 素材 ↔ 章节 ID 映射（2026-10-31 核查，写 `materials` 前必看）

| 学科 | 结论 |
|---|---|
| 高数·习题册 | 「综合题一~八」与上册 8 章**一一对应**：一 集合与函数、二 极限、三 函数的连续性、四 函数的导数与微分、五 导数与微分的应用举例、六 函数的积分、七 定积分的应用举例、八 常微分方程。下册另有同名文件（向量代数／多元微分／多元积分／无穷级数），**按文件名关键词排除** |
| 高数·课件 | 课件用的是**第二版章号**，不能直接对 ID：旧 5「微分中值定理」已并入第三版 **ch4**；第三版新增 **ch5**「导数与微分的应用举例」，课件第 5 章只讲到「函数图形的描绘」，**缺 kp04 曲率 / kp05 经济学应用**；旧 8「无穷级数」＝下册，**弃用**；旧 9「常微分方程」＝第三版 **ch8**，引用须写 mapping |
| 大物·习题册 | 第 1–10 章与大纲 1–10 章可对应（9 章气体运动论 ↔ 大纲 ch9；10 章热力学 ↔ 大纲 ch10）；**第 11–17 章（静电场→量子力学）属 A2，弃用** |
| 大物·课件 | 13 份（运动学／质点力学／动量／功与机械能／角动量／刚体／振动／波动／干涉／衍射／偏振／微观热学／宏观热学）全部落在 1–10 章内，无越界 |

逐章台账见 `data/intake/采集清单.csv`（18 行：每章课件、习题册、真题、目标题量、关键缺口），下载清单见 `source/下载清单.csv`。


---

## 二、双场景标签规范

题目必须能同时被两个场景筛到，字段只有三个：`scenario_tags` / `exam_hot` / `lecture_week`。

### 2.1 `scenario_tags`（数组，可多选）

| 值 | 含义 | 进入条件 | 前端用途 |
|---|---|---|---|
| `final_review` | 期末复习 | 该题知识点在**本课程期末范围内**，且属于该章主干（非拓展阅读） | 期末冲刺题单；按 `exam_hot` 优先排序 |
| `catch_up` | 跟课补漏 | 该题只依赖**单个知识点**或单章内容（不跨章综合），可在课后 20 分钟内做完 | 按 `lecture_week`/章序定位"这周讲到哪，就补哪" |

判定规则：

- 两标签**不是互斥**的。一道单章、且在本学期期末范围内的题，应同时标 `["final_review", "catch_up"]`。
- 跨两章以上的综合题、需要组合多个知识点的题，**只能标 `final_review`**。
- 纯计算技巧题、超纲题，两个都不标——即不进任何场景，不允许出现空数组占位。

### 2.2 `exam_hot`（布尔）

真实含义是「近年真题的高频考点」，**必须由真题统计得出，不允许凭感觉标**。

判定规则（按优先级）：

1. 该知识点在**近 5 年真题**中出现 ≥ 2 次 → `true`
2. 只出现 1 次 → `false`（保留为普通题）
3. 真题统计未覆盖到的章 → `false`，并在 `exams/` 里标注该章"未统计"，不要用"教材重点"冒充

### 2.3 `lecture_week`（整数，1–16）

指该知识点在**本校教学进度表**中的授课周次。当前状态：**未取得教务进度表**，因此：

- 该字段按章序线性估算填入，并**必须**同时写 `"lecture_week_source": "estimated"`
- 拿到官方进度表后，只改 `lecture_week` 与 `lecture_week_source`，不动其他字段
- 禁止在缺 `lecture_week_source` 的情况下填 `lecture_week`——这会被视为伪造进度数据

### 2.4 场景聚合方式

| 目录 | 聚合键 | 现状 |
|---|---|---|
| `catch_up/` | 章（`chapter` + `lecture_week`） | 按章聚合可用；周次维度待进度表接入 |
| `final_review/` | 章 / 知识点 + `exam_hot` | 按 `exam_hot` 排序可用 |

---

## 三、字段速查（题目）

| 字段 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `question_id` | ✓ | string | `math_a1c02_0001` 形式：学科_册章_序号，不用 UUID |
| `subject` | ✓ | string | `math` / `physics` |
| `knowledge_ids` | ✓ | string[] | 必须存在于 `taxonomy/` |
| `scenario_tags` | ✓ | string[] | 见 §2.1 |
| `difficulty` | ✓ | int 1–5 | 1 套公式直接得；2 一步变形；3 两步以上或需选方法；4 需组合两个知识点；5 竞赛/压轴或需构造 |
| `type` | ✓ | string | `choice` / `fill` / `calc` / `proof` / `draw` |
| `stem` | ✓ | string | 题干，公式用 LaTeX |
| `answer` | ✓ | string | 参考答案 |
| `source` | ✓ | string | 来源一句话，如"2022级高数A(1)期末 第3题 改编" |
| `license_note` | ✓ | string | `校内教学使用` / `CC-BY` / `自编改编` / `合成数据` |
| `assumptions` | 建议 | string[] | 本题依赖但题干**未声明**的假设——质疑场景的来源 |
| `error_tags` | 建议 | string[] | 见 §4 |
| `verify_hint` | 建议 | object\|null | `{expr, expected}`，可被符号计算验证 |
| `lecture_week` | 建议 | int | 见 §2.3，必须配 `lecture_week_source` |

---

## 四、错因词表（`error_tags`，12 类）

概念混淆 `concept_confusion` · 公式误用 `formula_misuse` · 条件遗漏 `condition_omitted` · 计算失误 `calculation_error` · 符号错误 `sign_error` · 单位量纲 `unit_dimension` · 思路缺失 `no_method` · 审题偏差 `misread_stem` · 多解漏解 `solution_missing` · 边界条件 `boundary_condition` · 未识别假设 `undefined_assumption` · 前置知识缺口 `prerequisite_gap`

---

## 五、版权与使用范围

- 题目：**优先改写，不逐字复制**；来源标注到「年份 + 题号 + 改编」
- 课件与教材：**只存元数据与页码定位**（`materials/`），不转载正文
- 真题：仅在答辩演示环境内使用，标注 `license_note: 校内教学使用`
- 合成数据：一律放 `synthetic/`，并在文件内标 `"synthetic": true`，保留生成脚本

## 五之二、`exam_hot` 是怎么算出来的（v1.0 起）

`exam_hot` **不是人工标的**，由 `scripts/tally_exam_hot.py` 从真题正文关键词统计得出，结果落在 `exams/exam_hot_*.json`，字段级可复核（每个考点都带 `hits_per_year` / `hit_years`）。

| 学科 | 底本 | 覆盖年份 | 粒级 | 结论 |
|---|---|---|---|---|
| 大物 | **试卷正文**（含「答案/参考/解答」的文件已排除） | 2012–2016、2018、2019、2022 = **8 年** | 知识点（38 个） | **27 个高频** |
| 高数 | **参考答案正文**（试卷本体全是扫描件，无文字层） | 17、18、19、20、23 级 = **5 年** | 章（8 章） | 7 个高频，仅 ch01 未命中 |

**三条必须一起交代的局限**（已写进各 `exam_hot_*.json` 的 `caveat`）：

1. **未覆盖的年份不参与计算，也不假装"没考"**：大物 2017/2020/2021 是扫描件、2023 只有含答案的 .doc；高数 16/21/22/24 级都是扫描件。这些年份列在 `excluded_years` 里。
2. 关键词法会漏掉纯公式题（如只写 `lim` 不写"极限"），所以 **`exam_hot=false` 只代表"没统计到"，不代表"没考过"**。
3. 高数底本是答案不是试卷，降级到章级，不能当知识点级结论用；换成扫描件 OCR 或拿到文字版试卷后重跑脚本即可升级。

---

## 六、题量、覆盖与冻结（v1.0）

**总量 45 题 = 高数 30 + 大物 15**，对齐 issue #24「高数 ≥30、大物 ≥15」。

| 学科 | 题量 | 章覆盖 | 每章题数 | `verify_hint` | 缺假设题 | 错因种类 |
|---|---|---|---|---|---|---|
| 高数 A1 | **30** | 8/8 | 3、4、3、4、4、4、4、4 | 26 | 1 | 9 |
| 大物 A1 | **15** | 10/10 | 1–2（力学相关章 2） | 8 | 2 | — |
| 合计 | **45** | 18/18 | — | **34** | 3 | 9 |

高数逐章：ch01 集合与函数 3、ch02 极限 4、ch03 连续性 3、ch04 导数微分 4、
ch05 导数应用 4、ch06 积分 4、ch07 定积分应用 4、ch08 常微分方程 4。

**为什么是 30 而不是更多**：范围已收缩到第 1 学期两门课（见 §一），高数上册 8 章、
教材正文 327 页，30 题对应每章 3–4 题，够 3 号做校验与冲突演示，也不至于把资料包做成题库。
issue #24 的「舒适区目标，可按计划微调但需说明」即指此，说明在此。

### 冻结规则（v1.0 起生效）

1. **`question_id` 冻结**：已发布的 ID 不改、不删。修正题干只改 `stem` / `answer`，ID 不动。
2. **新增只能追加**：新题用未占用的四位序号（如 `math_a1c05_0005`），不复用旧号。
3. **字段契约冻结**：`question_id / subject / knowledge_ids / scenario_tags / chapter / exam_hot /
   difficulty / type / stem / answer / assumptions / error_tags / verify_hint / source / license_note`
   十五个字段的名称与语义不再变更，2 号导入脚本可依赖。
4. **改字段要升版本**：确需变更字段语义时，README 版本号递增并在本表留痕，同时通知 2 号。

冻结日期：**2026-10-31**。此后至答辩结束，`data/questions/**` 只做「改错字」级别的修订。

### 错因标签覆盖（词表 12 类，当前题目覆盖 9 类）

`condition_omitted`（漏条件）、`formula_misuse`（公式误用）、`calculation_error`（计算错误）、
`concept_confusion`（概念混淆）、`undefined_assumption`（缺假设）、`boundary_condition`（边界/定义域）、
`sign_error`（符号错）、`solution_missing`（解不全）、`unit_dimension`（量纲/单位）。
完整词表见 §四。

---

## 七、版本

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-10-30 | 目录骨架、5+5 节点占位大纲、2 道样例题 |
| v0.2 | 2026-10-31 | 大纲改为真实数据（大物 10 章含学时／高数 14 章）；校验脚本补引用完整性检查；本 README 补依据、标签规范、字段表、错因词表 |
| v0.3 | 2026-10-31 | **高数大纲按教材目录页重建**：上册 9→**8 章**、下册 5→**7 章**，节级知识点 78 个并带页码，`verified` 转 true；新增 `textbook_map` / `textbook_only`（大物教材与大纲章号不一致，含教材独有的「几何光学」）；README 增页码字段口径 |
| v0.4 | 2026-10-31 | **范围收缩到第 1 学期**：高数只留《大学数学 1》上册（`nodes` 15→**8 章**、78→**40 知识点**），大物维持《大学物理学（Ⅰ）》1–10 章；两个 outline 升 v2.1 并新增顶层 `scope` / `scope.excluded_volume`（下册 7 章、A2 七章）；README 增「素材 ↔ 章节 ID 映射」（高数课件旧版章号错位、大物习题册 11–17 章弃用） |
| v0.5 | 2026-10-31 | **数据包补齐到可交付**：新增 `intake/collection_list`（18 章台账）、`materials/index.json`（57 条元数据）、`questions/physics_sample.json`（14 题）、高数样例题扩到 12 题、`exams/index.json`（58 份真题台账）、`exams/exam_hot_{physics,math}.json`（脚本统计，非人工标注）、`catch_up/`+`final_review/` 按章聚合；校验器扩到 materials/exams/exam_hot/场景四类；新增 4 个可复跑脚本 |
| **v1.0** | **2026-10-31** | **题量达舒适区并冻结**：高数 12→**30 题**（8 章全覆盖，每章 3–4 题，新增 18 题答案经数值复核）、大物维持 15 题，合计 **45 题**；新增 §六「题量与冻结」，`question_id` 与十五个字段契约冻结；**修复 `build_indexes.py` 知识点冒充章节的 bug**（曾把 `catch_up` 统计成 20 章，实为 16 章），`validate_schema.py` 增加「场景 `chapter_id` 必须是章级节点」的检查并反向验证可拦截；`physics_sample.json` 由 14 订正为 15 |
