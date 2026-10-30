#!/usr/bin/env python3
"""Rename Status「审核中」→ In Review; enrich all Issue bodies for AI handoff."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "AntonyTang-AT/Multi-agent_Learning_Planning_Assistant"
PROJECT_ID = "PVT_kwHOBU1eIc4BpdPU"

# Shared footer for AI-friendly issues
AI_HINT = """
## AI 协作提示（给执行者）

把 **本 Issue 全文** 与下列文档一起交给 AI，并要求「只改本 Issue 列出的目录，遵守技术栈与纪律，先跑通验收标准」：

- `README.md`
- `docs/技术路线与方案.md`
- `docs/项目文件结构.md`
- `docs/五人详细任务计划.md`
- 对应角色文档 `docs/roles/*.md`
- 相关接口：`docs/api.md` / `docs/agent-api.md`（按角色选用）

开分支命名建议：`feat/<issue-id>-short-slug`，完成后开 PR 到 `main`（需 Code Owner 审核）。
""".strip()


def load_token() -> None:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("GITHUB_TOKEN="):
            os.environ["GH_TOKEN"] = line.split("=", 1)[1].strip()
            os.environ.pop("GITHUB_TOKEN", None)
            return


def run(cmd: list[str], input_text: str | None = None) -> str:
    p = subprocess.run(
        cmd, input=input_text, check=False, text=True, capture_output=True, encoding="utf-8"
    )
    if p.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}\n{p.stderr or p.stdout}")
    return p.stdout


def gql(obj: dict) -> dict:
    tmp = Path(__file__).with_name("_gql_input.json")
    tmp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    data = json.loads(run(["gh", "api", "graphql", "--input", str(tmp)]))
    if "errors" in data:
        raise RuntimeError(json.dumps(data["errors"], ensure_ascii=False, indent=2))
    return data


def body(*sections: str) -> str:
    return "\n\n".join(s.strip() for s in sections if s and s.strip()) + "\n\n" + AI_HINT + "\n"


# ---------------------------------------------------------------------------
# Issue bodies keyed by number (must match current GitHub issue numbers)
# ---------------------------------------------------------------------------

ISSUES: dict[int, dict[str, str]] = {}


def _reg(n: int, title: str, text: str) -> None:
    ISSUES[n] = {"title": title, "body": text}


_reg(
    1,
    "[闸门][G0] 开工核对：栈已读 + 三端可空跑",
    body(
        """## 1. 任务目的
全组对齐「壳核分离」架构与锁定技术栈，确认仓库目录可用，避免后续各做各的选型。G0 是开工闸门：读完文档 + 三端至少能空跑或明确阻塞方案。""",
        """## 2. 具体要求与功能
- 全员阅读并确认锁定栈：前端 React+Vite+TS+AntD；后端 FastAPI+SQLite；Agent FastAPI+intent 路由+DeepSeek+SymPy；资料 UTF-8 JSON。
- 核对仓库已有目录：`frontend/` `backend/` `agent/` `data/` `docs/` `poster/` `pitch/`。
- 1/2/3 号各自尝试本地 hello：前端 `npm`、后端/Agent `uvicorn`；若工程未初始化，至少 README 与目录骨架就绪，并在 Issue 评论写明阻塞与 Mock 替代方案。
- 在 Issue 评论勾选验收，贴启动成功截图或说明。""",
        """## 3. 技术栈 / 方法
文档驱动核对；本机三进程端口约定：前端 `5173`、后端 `8000`、Agent `8001`。不引入 Docker/Vue/Streamlit。""",
        """## 4. 实现思路
1. 打开 `docs/技术路线与方案.md` §2 与 `docs/项目文件结构.md`，对照仓库树。
2. 各角色按自己目录检查 `.gitkeep` / README。
3. 能起则起最小服务；不能起则记录「缺 package.json / requirements」等，转入 F1/B1/A1。
4. 任意一人在本 Issue 汇总评论并勾验收。""",
        """## 5. 预期效果 / 验收标准
- [ ] 全组确认栈锁定，无并行选型争论
- [ ] 四大目录存在且文档入口可读
- [ ] 1/2/3 号要么可空跑，要么有明确阻塞+Mock 计划写在评论里""",
        """## 6. 主要修改 / 新增文件与目录
本闸门以**核对与评论**为主，一般不改代码。若发现缺目录可补：
- `frontend/` `backend/` `agent/` `data/` 及其 README
- 参考：`README.md`、`docs/技术路线与方案.md`、`docs/项目文件结构.md`、`docs/五人详细任务计划.md` §0""",
    ),
)

_reg(
    2,
    "[闸门][G1] 接口合同冻结：api.md + agent-api.md",
    body(
        """## 1. 任务目的
在写业务代码前冻结「后端业务 API」与「Agent I/O」合同，使前端 Mock、后端网关、Agent Worker 对着同一份 JSON 字段联调，减少返工。""",
        """## 2. 具体要求与功能
- 审阅并冻结一版 `docs/api.md`（session/materials/questions/plans/attempts/blackboard/ai/health）。
- 审阅并冻结一版 `docs/agent-api.md`（intent 枚举、status：ok/conflict/abstain/…、blackboard_entries、user_options）。
- 保证 `agent/examples/*.json` 可被前端 Mock 与后端转发直接参考。
- 之后任何字段变更必须在本 Issue（或新 Issue）评论通知 1/2/3 号。""",
        """## 3. 技术栈 / 方法
以 OpenAPI/Markdown 合同为准；Pydantic/TS 类型跟随文档，而不是反过来偷偷改字段。对齐 `docs/技术路线与方案.md` §4 Agent I/O。""",
        """## 4. 实现思路
1. 2 号主导业务 API 路径与 CRUD 形状；3 号主导 invoke 请求/响应。
2. 对照 examples 中 `create_plan` 样例，补齐缺字段说明。
3. 1 号旁听，确认 `frontend/src/types` 可摘类型。
4. 在评论写「冻结日期 + 版本备注」，勾验收。""",
        """## 5. 预期效果 / 验收标准
- [ ] `docs/api.md` 与实现意向一致（路径、关键字段齐全）
- [ ] `docs/agent-api.md` intent/status/黑板/选项齐全
- [ ] `agent/examples/*.json` 可拷贝联调
- [ ] 变更通知约定写清""",
        """## 6. 主要修改 / 新增文件与目录
- `docs/api.md`
- `docs/agent-api.md`
- `agent/examples/*.json`（必要时增补）
- 可选：`frontend/src/types/api.ts` 初稿、`backend/app/schemas/*`、`agent/app/schemas/*` 草稿
参考：`docs/技术路线与方案.md`、`docs/roles/02-后端.md`、`docs/roles/03-多智能体.md`""",
    ),
)

_reg(
    3,
    "[闸门][G2] 12号检查点：传统学习站可用（无 Agent）",
    body(
        """## 1. 任务目的
证明「壳」可独立交付：即使 Agent 未接通，用户仍能选场景、浏览资料、存计划、做题落库。这是 12 号硬闸门。""",
        """## 2. 具体要求与功能
- 前端主路径可点通（可接真后端，或 Mock 但需标注）。
- 后端 CRUD + 资料导入可用。
- 4 号资料包可被导入并查询非空。
- `/api/health` 在 agent down 时业务 API 不整站 500。""",
        """## 3. 技术栈 / 方法
前端 React+AntD；后端 FastAPI+SQLite；资料 JSON 导入。**禁止**依赖 Agent 才能完成 12 号演示。""",
        """## 4. 实现思路
1. 合并验收 F3 + B2/B3 + D3（或样例包）。
2. 刻意停掉 Agent，验证 health 与 CRUD。
3. 录 1–2 分钟屏：场景→资料→存计划→做题。
4. 截图/录屏贴本 Issue。""",
        """## 5. 预期效果 / 验收标准
- [ ] 无 Agent 主路径可演示
- [ ] 资料导入 + 查询可用
- [ ] agent down 时站点不崩
- [ ] 评论有录屏或关键截图""",
        """## 6. 主要修改 / 新增文件与目录
联调涉及（不一定本 Issue 直接改）：
- `frontend/src/pages/*` `frontend/src/api/*`
- `backend/app/api/*` `backend/app/services/import_data.py`
- `data/**`
参考：`docs/五人详细任务计划.md` §0 G2、`docs/演示脚本.md`""",
    ),
)

_reg(
    4,
    "[闸门][G3] 智能接通：冲突协商 + 校验弃答可录屏",
    body(
        """## 1. 任务目的
接通智能内核后，稳定演示两条创新链路：**计划审计冲突协商** 与 **校验失败弃答**，证明系统不偷偷改计划、不强行给错答。""",
        """## 2. 具体要求与功能
- `create_plan` → `status=conflict` → 展示 `user_options` → 用户裁决 → 可选 `arbitrate`。
- 出题/校验失败 → `status=abstain`（或等价），不把未校验答案当正解。
- 黑板条目在前端可见。
- 有可复现 request 样例（`demo.force_conflict` / `force_verify_fail`）。""",
        """## 3. 技术栈 / 方法
Agent：规则审计 + SymPy 校验 + DeepSeek（可降级模板）；后端仅转发；前端渲染 conflict/abstain。""",
        """## 4. 实现思路
1. 3 号保证 A2/A3 可稳定 curl。
2. 2 号网关透传并落库黑板/计划草稿。
3. 1 号渲染选项卡与弃答文案。
4. 用固定 examples 录屏，写入演示脚本。""",
        """## 5. 预期效果 / 验收标准
- [ ] 冲突协商链路可录屏复现
- [ ] 弃答链路可录屏复现
- [ ] 黑板可见
- [ ] 固定 request 样例入库""",
        """## 6. 主要修改 / 新增文件与目录
- `agent/app/workers/*` `agent/app/rules/*` `agent/examples/*` `agent/app/demos/*`
- `backend/app/api/ai_gateway.py` `backend/app/services/agent_client.py`
- `frontend/src/pages/Plan*` `Practice*` `components/UserOptions*` `Blackboard*`
参考：`docs/agent-api.md`、`docs/roles/03-多智能体.md`、`docs/演示脚本.md`""",
    ),
)

_reg(
    5,
    "[闸门][G4] 答辩冻结：三必演 + 海报 + 彩排",
    body(
        """## 1. 任务目的
答辩前冻结功能与材料：三必演可复现、海报可交、讲稿彩排达标，停止加人功能。""",
        """## 2. 具体要求与功能
- 三必演用例固定（冲突协商、校验弃答、错因/黑板等按脚本）。
- 产出 `poster/项目海报_A2.pdf`。
- 路演稿 + PPT；全员彩排 ≥2 次。
- 功能冻结：只修 blocker，不加人功能。""",
        """## 3. 技术栈 / 方法
演示脚本 + 固定 demo 开关；海报/PPT 按考核评分点组织叙事。""",
        """## 4. 实现思路
1. 5 号统筹材料；1/2/3 保证演示路径。
2. 对齐 `docs/演示脚本.md` 秒表。
3. 准备追问：安全、合成数据、与 ChatGPT 区别。
4. 本 Issue 贴彩排记录与文件链接。""",
        """## 5. 预期效果 / 验收标准
- [ ] 三必演 100% 可复现
- [ ] A2 PDF 可提交
- [ ] 彩排 ≥2；超时问题已消
- [ ] 明确宣布功能冻结""",
        """## 6. 主要修改 / 新增文件与目录
- `docs/演示脚本.md`
- `poster/项目海报_A2.pdf`
- `pitch/答辩PPT.pptx` `pitch/路演稿.md`
- `agent/examples/*` `agent/app/demos/*`（固化用例）
参考：`docs/roles/05-海报答辩.md`""",
    ),
)

_reg(
    6,
    "[前端][F1] Vite 工程初始化与路由布局",
    body(
        """## 1. 任务目的
在 `frontend/` 建立可运行的 React+TS 工程与基础布局，为后续页面与 Mock/联调提供容器。""",
        """## 2. 具体要求与功能
- 使用 Vite 创建 React-TS 项目。
- 安装并配置：`antd` `react-router-dom` `axios` `zustand`。
- `.env` / `.env.example`：`VITE_API_BASE`、`VITE_USE_MOCK`。
- 布局：顶栏 + 内容区。
- 路由空页：`/` `/chat` `/plan` `/practice` `/materials` `/blackboard`。
- `src/types/api.ts` 按 `docs/api.md` / agent 响应摘一版类型。""",
        """## 3. 技术栈 / 方法
**React 18 + Vite + TypeScript + Ant Design 5 + React Router 6 + Axios + Zustand**。包管理用 npm。""",
        """## 4. 实现思路
1. 在 `frontend/` 初始化（若目录已有 `.gitkeep`，就地创建，勿破坏仓库根）。
2. 配置 Ant Design、Router、基础 Layout。
3. 各路由先放占位 Typography/Empty。
4. 类型文件先写接口形状注释 + 核心 interface。
5. `npm run dev` 验证。""",
        """## 5. 预期效果 / 验收标准
- [ ] `npm run dev` 可开，顶栏+路由可切换
- [ ] 环境变量示例齐全
- [ ] `src/types/api.ts` 有初版""",
        """## 6. 主要修改 / 新增文件与目录
- `frontend/package.json` `frontend/vite.config.ts` `frontend/index.html`
- `frontend/.env.example`
- `frontend/src/main.tsx` `App.tsx`
- `frontend/src/pages/**`（占位页）
- `frontend/src/components/layout/**`
- `frontend/src/types/api.ts`
- `frontend/src/styles/**`
参考：`docs/roles/01-前端.md`、`docs/项目文件结构.md` §frontend""",
    ),
)

_reg(
    7,
    "[前端][F2] Mock 主路径：场景 / 计划冲突 / 黑板 / 练习",
    body(
        """## 1. 任务目的
在不依赖后端/Agent 的情况下，用 Mock 走通核心产品叙事：场景选择 → 计划冲突选项 → 黑板 → 练习状态（passed/abstain），保证 12 号前前端可演示。""",
        """## 2. 具体要求与功能
- `ScenarioWizard`：期末复习 / 跟课补漏；表单含考试日或章节、每日分钟、科目等。
- `PlanPage` + `UserOptionsCard`：展示三选项（延长时间/降深度/调目标）。
- `BlackboardPanel`：条目列表 + resolve 交互（可 Mock）。
- `PracticePage`：题干、提交、展示 `passed` / `abstain`。
- `src/mocks` 基于 `agent/examples` 改编；`VITE_USE_MOCK=true` 开关。""",
        """## 3. 技术栈 / 方法
React + Ant Design Form/Card/List；本地 JSON Mock；Zustand 存当前场景与计划草稿。""",
        """## 4. 实现思路
1. 复制/改编 `agent/examples/create_plan_final_review.json` 到 `src/mocks`。
2. Mock 层模拟 conflict 与 abstain 两种响应。
3. 页面只读 Mock client，接口形状与未来真 API 一致，便于 F3 替换。
4. 自测：从首页点到选项裁决再到黑板。""",
        """## 5. 预期效果 / 验收标准
- [ ] 关后端也能走通场景→冲突选项→黑板→练习状态
- [ ] Mock 开关可用
- [ ] 组件命名与目录清晰，便于联调替换""",
        """## 6. 主要修改 / 新增文件与目录
- `frontend/src/pages/Scenario*` `Plan*` `Practice*` `Materials*` `Blackboard*`
- `frontend/src/components/ScenarioWizard*` `UserOptionsCard*` `BlackboardPanel*`
- `frontend/src/mocks/**`
- `frontend/src/stores/**`
- `frontend/src/api/client.ts`（可先返回 mock）
参考：`agent/examples/*`、`docs/agent-api.md`、`docs/roles/01-前端.md`""",
    ),
)

_reg(
    8,
    "[前端][F3] 对接后端 CRUD（12号传统站）",
    body(
        """## 1. 任务目的
关闭或旁路 Mock，对接真实后端 CRUD，完成 12 号「传统学习站」前端侧：浏览资料、存计划、做题落库。""",
        """## 2. 具体要求与功能
- `api/client.ts`：baseURL、拦截器、错误 Toast（AntD message/notification）。
- 对接：`session` `materials` `questions` `plans` `attempts` `blackboard`。
- 无 AI 时仍可完成主路径；Agent 不可用不阻塞 CRUD。
- 与后端字段不一致时当日对齐 `docs/api.md` / types。""",
        """## 3. 技术栈 / 方法
Axios + React Query 可选（非必须）；优先 Axios + Zustand。类型与 `docs/api.md` 对齐。""",
        """## 4. 实现思路
1. 等 B2/B3 就绪；阻塞时保留 Mock 分支。
2. 逐页替换数据源：先 materials/questions，再 plans/attempts/blackboard。
3. 统一错误处理与 loading。
4. 与 2 号联调 checklist 打勾。""",
        """## 5. 预期效果 / 验收标准
- [ ] `VITE_USE_MOCK=false` 主路径可走通
- [ ] 资料/计划/作答可读写
- [ ] 错误有提示，不白屏""",
        """## 6. 主要修改 / 新增文件与目录
- `frontend/src/api/client.ts` `frontend/src/api/*.ts`
- `frontend/src/types/api.ts`
- `frontend/src/pages/**`（接真数据）
- `frontend/.env.example`
参考：`docs/api.md`、`docs/roles/01-前端.md`""",
    ),
)

_reg(
    9,
    "[前端][F4] 对接 AI 网关：冲突与弃答真数据",
    body(
        """## 1. 任务目的
对接 `POST /api/ai/{intent}`，用真实 Agent 响应渲染冲突选项、弃答与黑板，完成智能接通后的前端表现。""",
        """## 2. 具体要求与功能
- 调用 AI 网关：`create_plan` / `arbitrate` / `verify_answer` 等。
- 正确渲染 `conflict` + `user_options`，提交用户裁决。
- 正确渲染 `abstain` / 提示模式文案（不把未校验答案当正确）。
- DemoBar：`time-jump`、force 开关（若后端提供）。""",
        """## 3. 技术栈 / 方法
Axios 调 backend 网关（**前端不直连 Agent**）；状态机用页面状态或 Zustand。""",
        """## 4. 实现思路
1. 复用 F2 组件，数据源改为网关响应。
2. 裁决后调后端存结果，必要时二次 invoke。
3. 处理 `agent_unavailable` 友好提示。
4. 与 G3 录屏路径对齐。""",
        """## 5. 预期效果 / 验收标准
- [ ] 真数据下冲突/弃答 UI 正确
- [ ] 裁决可提交并回显
- [ ] DemoBar 可用或有明确「未提供」说明""",
        """## 6. 主要修改 / 新增文件与目录
- `frontend/src/api/ai.ts`
- `frontend/src/pages/Plan*` `Practice*`
- `frontend/src/components/UserOptionsCard*` `DemoBar*`
- `frontend/src/types/api.ts`
参考：`docs/api.md`（ai 段）、`docs/agent-api.md`""",
    ),
)

_reg(
    10,
    "[前端][F5] 演示模式与 3 分钟操作路径稳定",
    body(
        """## 1. 任务目的
把前端打磨到答辩可用：3 分钟内稳定点完必演操作，投屏可读，与讲稿对齐。""",
        """## 2. 具体要求与功能
- UI 投屏友好：字号、对比度、中文文案。
- 演示控制条可用（跳转关键状态/触发 demo）。
- 与 5 号合写并演练 `docs/演示脚本.md`。
- 答辩前冻结页面，不加人功能。""",
        """## 3. 技术栈 / 方法
现有 React/AntD；可用路由 query 或 DemoBar 切演示态。""",
        """## 4. 实现思路
1. 按脚本列出点击序列，缺页补齐。
2. 固定演示账号/种子数据依赖告知 2 号。
3. 全员走表计时，修卡顿与文案。
4. 冻结前开 PR 只含演示修复。""",
        """## 5. 预期效果 / 验收标准
- [ ] 3 分钟路径稳定可复现
- [ ] 投屏文案可读
- [ ] 演示脚本与 UI 一致
- [ ] 功能冻结声明""",
        """## 6. 主要修改 / 新增文件与目录
- `frontend/src/components/DemoBar*`
- `frontend/src/pages/**`（文案/样式）
- `frontend/src/styles/**`
- 协作：`docs/演示脚本.md` `pitch/路演稿.md`
参考：`docs/roles/01-前端.md`、`docs/roles/05-海报答辩.md`""",
    ),
)

_reg(
    11,
    "[后端][B1] FastAPI 骨架：health / session / CORS",
    body(
        """## 1. 任务目的
在 `backend/` 搭好传统 Web API 骨架，提供健康检查、会话入口与 CORS，作为后续 CRUD 与网关的底座。""",
        """## 2. 具体要求与功能
- `venv` + `requirements.txt`：fastapi uvicorn sqlalchemy pydantic httpx python-dotenv 等。
- `app/main.py` 挂路由；CORS 放行 `http://localhost:5173`。
- models 初版：User 等核心表。
- `GET /api/health`；`POST /api/session`。
- OpenAPI `/docs` 可打开。""",
        """## 3. 技术栈 / 方法
**Python 3.11+ · FastAPI · Pydantic v2 · SQLAlchemy 2 · SQLite · uvicorn**。纪律：不写提示词/Agent 逻辑；不放 LLM Key。""",
        """## 4. 实现思路
1. 初始化包结构对齐 `docs/项目文件结构.md`。
2. config 读 `.env`：`DATABASE_URL` `AGENT_BASE_URL`。
3. health 返回服务状态；session 创建/返回简易 user/session id。
4. 本地 curl 验证。""",
        """## 5. 预期效果 / 验收标准
- [ ] `/api/health` 绿
- [ ] `/docs` 可开
- [ ] CORS 下前端可跨域访问
- [ ] session 可创建""",
        """## 6. 主要修改 / 新增文件与目录
- `backend/requirements.txt` `backend/.env.example`
- `backend/app/main.py` `config.py`
- `backend/app/db/session.py` `models.py`
- `backend/app/api/health.py` `session.py`
- `backend/app/schemas/**`
参考：`docs/roles/02-后端.md`、`docs/api.md`""",
    ),
)

_reg(
    12,
    "[后端][B2] 资料导入与 materials/questions 查询",
    body(
        """## 1. 任务目的
把 `data/` 结构化资料导入 SQLite，并提供材料/题目查询 API，支撑传统站浏览与后续 Agent resource_refs。""",
        """## 2. 具体要求与功能
- `services/import_data.py`：读 taxonomy + questions（及 materials）。
- `GET /api/materials`、`GET /api/questions`，支持 `subject` / `chapter` / `scenario_tag` 等过滤。
- 同步更新 `docs/api.md`。
- 导入仓库样例后查询非空。""",
        """## 3. 技术栈 / 方法
SQLAlchemy 批量写入；JSON 文件读取；与 4 号 schema 对齐；可用 `backend/scripts/seed_or_import.py`。""",
        """## 4. 实现思路
1. 先支持现有 `data/questions/math_sample.json` 与 taxonomy。
2. 幂等导入（按 id upsert）。
3. 查询参数写清默认值与示例。
4. 手工/单测验证过滤。""",
        """## 5. 预期效果 / 验收标准
- [ ] 一键/脚本导入成功
- [ ] 过滤查询非空
- [ ] `docs/api.md` 已同步""",
        """## 6. 主要修改 / 新增文件与目录
- `backend/app/services/import_data.py`
- `backend/app/api/materials.py` `questions.py`
- `backend/app/db/models.py`
- `backend/scripts/seed_or_import.py`
- `docs/api.md`
参考：`data/README.md`、`data/scripts/validate_schema.py`""",
    ),
)

_reg(
    13,
    "[后端][B3] 计划 / 作答 / 黑板 CRUD",
    body(
        """## 1. 任务目的
完成计划、作答、黑板的持久化读写与 resolve，支撑 12 号无 AI 联调与后续 AI 结果落库。""",
        """## 2. 具体要求与功能
- plans：GET/PUT（保存用户计划快照）。
- attempts：POST（作答记录）。
- blackboard：GET + resolve（更新 status/resolution）。
- 与前端 F3 联调通过（G2）。""",
        """## 3. 技术栈 / 方法
FastAPI 路由 + SQLAlchemy 模型；Pydantic schema；事务内更新 resolve。""",
        """## 4. 实现思路
1. 按 `docs/api.md` 定字段。
2. 计划以 JSON 字段存草案亦可（注明结构）。
3. resolve 只改存储，不做智能消冲突。
4. 提供 curl 示例给前端。""",
        """## 5. 预期效果 / 验收标准
- [ ] plans/attempts/blackboard 读写可用
- [ ] resolve 生效
- [ ] 与前端无 AI 路径联调通过""",
        """## 6. 主要修改 / 新增文件与目录
- `backend/app/api/plans.py` `attempts.py` `blackboard.py`
- `backend/app/db/models.py`
- `backend/app/schemas/**`
- `docs/api.md`
参考：`docs/roles/02-后端.md`""",
    ),
)

_reg(
    14,
    "[后端][B4] Agent 网关：httpx 转发与降级错误码",
    body(
        """## 1. 任务目的
实现唯一 AI 出口：用 httpx 把请求转发到 Agent `:8001`，失败时返回明确错误码，且 Agent 宕机不影响 CRUD。""",
        """## 2. 具体要求与功能
- `services/agent_client.py`：超时、错误映射。
- `POST /api/ai/{intent}`：组装/透传 body → agent invoke → 返回。
- `GET /api/health` 含 `agent: up|down`。
- **禁止**在网关写智能分支（如自动消冲突、改写答案）。""",
        """## 3. 技术栈 / 方法
httpx 异步或同步客户端；配置仅 `AGENT_BASE_URL`；错误码如 `agent_unavailable`。""",
        """## 4. 实现思路
1. client 封装 `POST {AGENT_BASE_URL}/agent/v1/invoke`。
2. 网关校验 intent 白名单后转发。
3. 连接失败返回 503 + 业务错误码，不 500 打爆整站。
4. health 探测 agent `/health`。""",
        """## 5. 预期效果 / 验收标准
- [ ] Agent 启动时可调通
- [ ] Agent 关闭时返回 `agent_unavailable`，CRUD 仍可用
- [ ] health 正确显示 up/down
- [ ] 无智能分支代码""",
        """## 6. 主要修改 / 新增文件与目录
- `backend/app/services/agent_client.py`
- `backend/app/api/ai_gateway.py`
- `backend/app/api/health.py`
- `backend/.env.example`
- `docs/api.md`
参考：`docs/agent-api.md`、`docs/roles/02-后端.md`""",
    ),
)

_reg(
    15,
    "[后端][B5] AI 响应落库 + demo 接口 + 种子库",
    body(
        """## 1. 任务目的
把 AI 响应可靠落库，提供演示辅助接口与答辩种子库，保证现场可恢复。""",
        """## 2. 具体要求与功能
- 落库：AiCallLog、blackboard_entries、plan 草稿快照。
- `POST /api/demo/time-jump`（及必要 demo 辅助）。
- 导入 4 号扩容资料后回归。
- 准备 `demo.db`（或种子脚本）供答辩。""",
        """## 3. 技术栈 / 方法
SQLAlchemy；网关成功后写库；demo 接口只改演示时钟/快照，不写智能。""",
        """## 4. 实现思路
1. 在 ai_gateway 成功路径写日志与黑板。
2. time-jump 更新会话演示偏移或转给 agent demo 字段。
3. 导出/复制一份干净 SQLite。
4. README 写清恢复步骤。""",
        """## 5. 预期效果 / 验收标准
- [ ] AI 调用可追溯
- [ ] 黑板/计划草稿可查
- [ ] demo 接口可用
- [ ] 种子库可一键恢复""",
        """## 6. 主要修改 / 新增文件与目录
- `backend/app/api/ai_gateway.py` `demo.py`
- `backend/app/db/models.py`（AiCallLog 等）
- `backend/scripts/seed_or_import.py`
- `backend/README.md`
参考：`docs/api.md`、`docs/演示脚本.md`""",
    ),
)

_reg(
    16,
    "[Agent][A1] 服务骨架：health + invoke 回声",
    body(
        """## 1. 任务目的
在 `agent/` 建立独立智能内核服务骨架：健康检查 + `invoke` 入口回声，冻结 request/response schema，供后端网关联调。""",
        """## 2. 具体要求与功能
- FastAPI 应用；`.env.example` 含 `DEEPSEEK_API_KEY` `MODEL_NAME`。
- `GET /health`；`POST /agent/v1/invoke`。
- schemas 对齐 `docs/agent-api.md` / 技术路线 §4。
- 未知 intent 返回明确错误；可提供临时 `echo` 调试意图。
- 编排方式：intent 路由 + Worker；**不强制 CrewAI**。""",
        """## 3. 技术栈 / 方法
FastAPI + Pydantic v2；可选 openai 兼容客户端连 DeepSeek；端口 `8001`。""",
        """## 4. 实现思路
1. 按项目文件结构建 `app/api` `schemas` `orchestrator` `workers` 空模块。
2. invoke 校验 body → 路由表 → echo 返回原 input。
3. 与 `agent/examples` 对照字段名。
4. README 写启动命令。""",
        """## 5. 预期效果 / 验收标准
- [ ] `/health` 可用
- [ ] invoke 回声成功
- [ ] 未知 intent 有明确错误
- [ ] schema 文档一致""",
        """## 6. 主要修改 / 新增文件与目录
- `agent/requirements.txt` `agent/.env.example` `agent/README.md`
- `agent/app/main.py` `config.py`
- `agent/app/api/invoke.py`
- `agent/app/schemas/request.py` `response.py`
- `agent/app/orchestrator/**`
参考：`docs/roles/03-多智能体.md`、`docs/agent-api.md`""",
    ),
)

_reg(
    17,
    "[Agent][A2] create_plan + 规则审计冲突 + user_options",
    body(
        """## 1. 任务目的
实现计划生成与**规则审计**：不可行计划必须暴露为 `conflict` + 黑板 + 三选项，支持用户裁决；可用 `demo.force_conflict` 稳定演示。""",
        """## 2. 具体要求与功能
- `workers/planner.py`：生成计划草案（规则/模板优先，LLM 可选）。
- `rules/plan_audit.py`：超时、缺完成标准、先修冲突等确定性检查。
- 冲突时：`status=conflict`，写 `blackboard_entries`，返回 `user_options`（延长时间/降深度/调目标）。
- `arbitrate`：按 `option_id` 重排或降级说明。
- 更新 `examples/create_plan_*.json` 与真响应一致。""",
        """## 3. 技术栈 / 方法
规则优先于模型；DeepSeek 仅润色/生成任务文案；无 Key 时模板降级仍可演示。""",
        """## 4. 实现思路
1. planner 根据 scenario（final_review/catch_up）产出天级任务列表。
2. audit 计算每日负荷 vs constraints；触发冲突。
3. force_conflict 短路审计结果便于录屏。
4. arbitrate 读取选项修改 plan 后再返回 ok。""",
        """## 5. 预期效果 / 验收标准
- [ ] 正常约束可返回 ok 计划
- [ ] 冲突路径稳定可复现
- [ ] user_options 三选项齐全
- [ ] examples 与实现一致""",
        """## 6. 主要修改 / 新增文件与目录
- `agent/app/workers/planner.py`
- `agent/app/rules/plan_audit.py`
- `agent/app/orchestrator/**`（路由 create_plan/arbitrate）
- `agent/app/blackboard/**`
- `agent/examples/create_plan_*.json`
参考：`docs/技术路线与方案.md` §3.1、`docs/agent-api.md`""",
    ),
)

_reg(
    18,
    "[Agent][A3] 出题/校验链路 + 弃答降级",
    body(
        """## 1. 任务目的
实现出题与计算检验质量门禁：校验失败则重试→提示→`abstain`，绝不把未校验/错误答案硬当正解；支持 `force_verify_fail` 演示。""",
        """## 2. 具体要求与功能
- `workers/verifier.py`：SymPy/规则校验。
- `workers/generator.py`：优先基于 `resource_payload` 改编题。
- 失败链路与 `audit_trail`、弃答文案。
- 稳定端口与 README 供 2 号联调。""",
        """## 3. 技术栈 / 方法
SymPy + 少量规则表；LLM 生成后必须过 verifier；演示开关 `demo.force_verify_fail`。""",
        """## 4. 实现思路
1. generate_question / verify_answer 两个 intent。
2. verifier 对表达式/数值题给出 pass/fail + 原因。
3. fail 时降级策略写清；最终 abstain。
4. 单测覆盖力所能及的符号题。""",
        """## 5. 预期效果 / 验收标准
- [ ] 校验通过可返回题目/结论
- [ ] 失败可走到 abstain
- [ ] force_verify_fail 可演示
- [ ] 后端可稳定调用""",
        """## 6. 主要修改 / 新增文件与目录
- `agent/app/workers/verifier.py` `generator.py`
- `agent/app/orchestrator/**`
- `agent/examples/*verify*`（可新建）
- `agent/tests/**`
- `agent/README.md`
参考：`docs/roles/03-多智能体.md`、`docs/agent-api.md`""",
    ),
)

_reg(
    19,
    "[Agent][A4] 错因策略差异 + 黑板条目齐全",
    body(
        """## 1. 任务目的
同一知识点在不同错因下给出可区分的推荐/计划插入策略；黑板类型尽量覆盖 conflict/challenge/intervention；无 Key 仍可模板演示。""",
        """## 2. 具体要求与功能
- 错因 → 策略规则表（字典即可）。
- 切换 `error_tag` 后策略/计划块明显不同。
- 黑板条目类型能出则出。
- 与 2 号联调 create_plan / verify。""",
        """## 3. 技术栈 / 方法
规则表驱动；可选 LLM 生成解释文案；降级模板。""",
        """## 4. 实现思路
1. 定义 ≥4 种错因（与 4 号资料对齐）。
2. 策略表映射到复习动作（回顾概念/变式题/先修回炉等）。
3. 在 create_plan 或独立 intent 中注入。
4. 写对比 example 方便前端展示。""",
        """## 5. 预期效果 / 验收标准
- [ ] 不同错因策略可区分
- [ ] 黑板类型有覆盖
- [ ] 无 Key 可演示
- [ ] 与后端联调通过""",
        """## 6. 主要修改 / 新增文件与目录
- `agent/app/rules/error_strategy.py`（或同级规则文件）
- `agent/app/workers/planner.py` / `memory.py`
- `agent/app/blackboard/**`
- `agent/examples/**`
参考：`data/` 错因字段、`docs/五人详细任务计划.md` §3""",
    ),
)

_reg(
    20,
    "[Agent][A5] 演示用例固化 + 质疑/干预（增强）",
    body(
        """## 1. 任务目的
把答辩三必演做成 100% 可复现的固定用例；有余力补齐质疑/元认知/主动干预；可选 CrewAI 包装但不改 I/O。""",
        """## 2. 具体要求与功能
- 固定 request 文件/一键脚本。
- Evaluator 结构化质疑（对接 4 号缺假设题）。
- 元认知 / 主动干预模板卡片。
- （可选）CrewAI 包装，I/O 不变。""",
        """## 3. 技术栈 / 方法
`agent/app/demos` + examples；规则触发质疑；LLM 可选。""",
        """## 4. 实现思路
1. 把 G3 两条链路 + 错因对比写成 demos。
2. challenge / metacognitive_feedback / proactive_intervention intent。
3. 脚本对比实际响应与金样。
4. 文档写清答辩操作命令。""",
        """## 5. 预期效果 / 验收标准
- [ ] 三必演一键/固定文件可复现
- [ ] 增强能力有则演示、无则不强行写海报
- [ ] I/O 未被可选框架破坏""",
        """## 6. 主要修改 / 新增文件与目录
- `agent/app/demos/**`
- `agent/app/workers/evaluator.py`
- `agent/examples/**`
- `agent/README.md`
- 协作：`docs/演示脚本.md`
参考：`docs/roles/03-多智能体.md`""",
    ),
)

_reg(
    21,
    "[资料][D1] 高数+大物章级大纲对齐课表",
    body(
        """## 1. 任务目的
把高数与大物章级大纲改到与本校教材/课表一致，作为后续材料、习题、场景标签的骨架。""",
        """## 2. 具体要求与功能
- 修订 `taxonomy/math_outline.json` 与 `physics_outline.json`。
- 先修关系合理。
- README 注明依据教材版本。""",
        """## 3. 技术栈 / 方法
UTF-8 JSON；保持 id 稳定（已有引用勿乱改）；人工对照课表。""",
        """## 4. 实现思路
1. 打开现有 outline，按课表改章名/顺序。
2. 补先修边。
3. 跑校验脚本（若已覆盖 taxonomy）。
4. 在 `data/README.md` 写教材版本。""",
        """## 5. 预期效果 / 验收标准
- [ ] 两份 outline 章名对齐课表
- [ ] 先修合理
- [ ] README 有版本说明""",
        """## 6. 主要修改 / 新增文件与目录
- `data/taxonomy/math_outline.json`
- `data/taxonomy/physics_outline.json`
- `data/README.md`
参考：`docs/roles/04-资料整理.md`、`data/schemas/`""",
    ),
)

_reg(
    22,
    "[资料][D2] 双场景标签规范 + 可导入样例包",
    body(
        """## 1. 任务目的
定义期末复习/跟课补漏双场景标签规范，并交付可被校验脚本与后端导入的样例题包。""",
        """## 2. 具体要求与功能
- 规范写入 `data/README.md`：`scenario_tags` / `exam_hot` / `lecture_week`。
- 高数样例 ≥8 题；大物样例 ≥5 题。
- `python data/scripts/validate_schema.py` 通过。""",
        """## 3. 技术栈 / 方法
JSON schema/约定字段；validate_schema.py；与后端 import 字段对齐。""",
        """## 4. 实现思路
1. 先写半页规范再扩题。
2. 每题含章节、场景标签、必要 verify_hint。
3. 跑校验，修报错。
4. 通知 2 号可试导入。""",
        """## 5. 预期效果 / 验收标准
- [ ] README 规范清晰
- [ ] 题量达标
- [ ] 校验脚本通过""",
        """## 6. 主要修改 / 新增文件与目录
- `data/README.md`
- `data/questions/math_sample.json`（扩）
- `data/questions/physics_sample.json`（新建/扩）
- `data/scripts/validate_schema.py`（若需补规则）
参考：`docs/roles/04-资料整理.md`""",
    ),
)

_reg(
    23,
    "[资料][D3] 资料包 v0.1：材料元数据 + 习题 + 真题入口",
    body(
        """## 1. 任务目的
交付 12 号可用的资料包 v0.1：每章材料入口、可校验习题、真题可检索，并含缺假设/错因样例支撑智能演示。""",
        """## 2. 具体要求与功能
- `materials/` 每章至少 1 条元数据。
- 习题优先填 `verify_hint`、错因、期末热点。
- `exams/` 高数 ≥1 套元数据/拆题。
- 跟课 `lecture_week` 聚合与期末 `exam_hot` 可筛。
- 缺假设样例 ≥2；错因种类 ≥4。""",
        """## 3. 技术栈 / 方法
结构化 JSON；版权仅摘录元数据/短摘；合成数据标 `synthetic`。""",
        """## 4. 实现思路
1. 按 outline 扫章建 materials。
2. 扩 questions，对齐 D2 标签。
3. exams 能检索即可。
4. 打包说明写给 2 号导入。""",
        """## 5. 预期效果 / 验收标准
- [ ] v0.1 可导入
- [ ] 场景筛选可用
- [ ] 缺假设/错因达标
- [ ] 校验通过""",
        """## 6. 主要修改 / 新增文件与目录
- `data/materials/**`
- `data/questions/**`
- `data/exams/**`
- `data/catch_up/**` 或标签齐全即可
- `data/final_review/**`（可选）
- `data/README.md`
参考：`docs/五人详细任务计划.md` §4""",
    ),
)

_reg(
    24,
    "[资料][D4] 扩容至舒适区并冻结 data v1.0",
    body(
        """## 1. 任务目的
题量扩到舒适区并冻结版本，保证答辩期不改 ID，且覆盖 3 号校验/冲突演示知识点。""",
        """## 2. 具体要求与功能
- 高数 ≥30、大物 ≥15（舒适区目标，可按计划微调但需说明）。
- 大物迁移章补齐。
- 与 3 号对验收覆盖点。
- README 版权终版；标记 `data v1.0`；冻结后不改 ID。""",
        """## 3. 技术栈 / 方法
继续 JSON + validate；版本号写在 README。""",
        """## 4. 实现思路
1. 在 v0.1 上扩题，保留旧 id。
2. 列演示用知识点 checklist 与 3 号对表。
3. 打版本标签/写明冻结日。
4. 通知 2 号回归导入。""",
        """## 5. 预期效果 / 验收标准
- [ ] 题量达舒适区或有书面说明
- [ ] 演示覆盖确认
- [ ] v1.0 冻结声明
- [ ] 校验通过""",
        """## 6. 主要修改 / 新增文件与目录
- `data/questions/**` `data/materials/**` `data/exams/**`
- `data/README.md`
参考：`docs/roles/04-资料整理.md`""",
    ),
)

_reg(
    25,
    "[答辩][P1] 用户访谈 + 双场景痛点 + 双方案比较表",
    body(
        """## 1. 任务目的
用真实用户声音论证「期末复习 / 跟课补漏」需求，并完成方案 A/B 五维比较，支撑海报与路演开场。""",
        """## 2. 具体要求与功能
- 访谈/问卷 ≥5 人（两场景都要问到）。
- 痛点 3 条原话级素材。
- 比较表：可行性/实用/创新/安全/成本。
- 与 3 号对齐创新表述（**不写代码没有的功能**）。""",
        """## 3. 技术栈 / 方法
问卷/访谈记录；表格文档；对齐形式化方案中的创新点（质疑/校验/协商）。""",
        """## 4. 实现思路
1. 设计 5–8 个问题。
2. 收集原话，提炼痛点。
3. 填比较表，标明本方案优势对应到功能。
4. 存入 pitch 备忘。""",
        """## 5. 预期效果 / 验收标准
- [ ] ≥5 人访谈记录可追溯
- [ ] 3 条痛点原话
- [ ] 比较表定稿
- [ ] 创新表述已与 3 号对齐""",
        """## 6. 主要修改 / 新增文件与目录
- `pitch/个人贡献备忘.md` 或 `pitch/用户访谈记录.md`（新建）
- `pitch/` 下比较表 md/xlsx
参考：`docs/roles/05-海报答辩.md`、`docs/学习计划多智能体系统·形式化整体方案.md`""",
    ),
)

_reg(
    26,
    "[答辩][P2] 海报线框 + PPT 大纲 + 路演稿初稿",
    body(
        """## 1. 任务目的
产出可评审的 A2 海报线框、PPT 大纲与带秒表的路演稿初稿，并开始收集个人贡献表述。""",
        """## 2. 具体要求与功能
- 海报线框（A2 七块，见 roles/05）。
- PPT 大纲 8–10 页。
- `pitch/路演稿.md` 初稿含秒表分节。
- 收齐 1/2/3/4 贡献各 3–5 句。""",
        """## 3. 技术栈 / 方法
Figma/PPT/Markdown 任一；结构服从评分点：需求、方案、架构、创新、演示、分工。""",
        """## 4. 实现思路
1. 按七块搭线框文字。
2. PPT 大纲映射 3 分钟叙事。
3. 路演稿与演示脚本预留接口。
4. 群里催贡献备忘。""",
        """## 5. 预期效果 / 验收标准
- [ ] 线框可评审
- [ ] PPT 大纲齐全
- [ ] 路演稿有秒表
- [ ] 贡献收集中/已收""",
        """## 6. 主要修改 / 新增文件与目录
- `poster/`（线框图或说明）
- `pitch/答辩PPT.pptx`（可先大纲 md）
- `pitch/路演稿.md`
- `pitch/个人贡献备忘.md`
参考：`docs/roles/05-海报答辩.md`""",
    ),
)

_reg(
    27,
    "[答辩][P3] 评分点自检 + 用现有截图更新线框",
    body(
        """## 1. 任务目的
对照考核评分点自检材料完整性，并用现有 Mock/真机截图更新海报线框与架构图占位。""",
        """## 2. 具体要求与功能
- 需求/比较/创新/分工在材料中均有着落。
- 用截图更新线框中的 UI/架构图位置。
- 列出缺项清单并指派。""",
        """## 3. 技术栈 / 方法
评分表对照；截图来自前端 Mock 或联调环境。""",
        """## 4. 实现思路
1. 打印评分点 checklist。
2. 缺图就找 1 号截；缺创新表述找 3 号。
3. 更新线框文件。
4. 本 Issue 贴自检表。""",
        """## 5. 预期效果 / 验收标准
- [ ] 自检表完成
- [ ] 线框截图位已更新
- [ ] 缺项有负责人""",
        """## 6. 主要修改 / 新增文件与目录
- `poster/**`
- `pitch/**`
- `docs/` 下可放自检表副本
参考：考核表、`docs/roles/05-海报答辩.md`""",
    ),
)

_reg(
    28,
    "[答辩][P4] A2 PDF + PPT 终稿 + 全员彩排",
    body(
        """## 1. 任务目的
交付可提交的 A2 PDF、PPT/讲稿终稿，完成全员彩排与追问准备，与真机演示对齐。""",
        """## 2. 具体要求与功能
- `poster/项目海报_A2.pdf`。
- PPT 终稿；路演稿终稿。
- 真机截图：冲突/弃答/黑板。
- 全员彩排 ≥2；演示脚本与口播对齐。
- 追问准备：安全、合成数据、与 ChatGPT 区别。""",
        """## 3. 技术栈 / 方法
导出 PDF；按 `docs/演示脚本.md` 走表；材料只描述已实现功能。""",
        """## 4. 实现思路
1. 替换所有占位图为真机图。
2. 与 1/3 号对秒表。
3. 彩排记录问题清单并清零。
4. 打包提交物清单。""",
        """## 5. 预期效果 / 验收标准
- [ ] PDF 可提交
- [ ] PPT/讲稿终稿
- [ ] 彩排 ≥2 且不超时
- [ ] 追问应答稿就绪""",
        """## 6. 主要修改 / 新增文件与目录
- `poster/项目海报_A2.pdf`
- `pitch/答辩PPT.pptx`
- `pitch/路演稿.md`
- `docs/演示脚本.md`
参考：`docs/roles/05-海报答辩.md`、G4""",
    ),
)


def rename_status_option() -> None:
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
    field = None
    for f in data["data"]["node"]["fields"]["nodes"]:
        if f and f.get("name") == "Status":
            field = f
            break
    if not field:
        raise RuntimeError("Status field not found")

    print("Before:", [o["name"] for o in field["options"]])
    color_ok = {
        "GRAY",
        "BLUE",
        "GREEN",
        "YELLOW",
        "ORANGE",
        "RED",
        "PINK",
        "PURPLE",
    }
    new_opts = []
    for o in field["options"]:
        name = o["name"]
        if name in ("审核中", "In Review"):
            name = "In Review"
        color = o.get("color") or "GRAY"
        if color not in color_ok:
            color = "YELLOW" if name == "In Review" else "GRAY"
        desc = o.get("description") or ""
        if name == "In Review":
            desc = "Awaiting Code Owner / lead review"
        new_opts.append(
            {"id": o["id"], "name": name, "color": color, "description": desc}
        )

    # If somehow missing, append
    if not any(o["name"] == "In Review" for o in new_opts):
        # insert before Done
        done_idx = next((i for i, o in enumerate(new_opts) if o["name"] == "Done"), len(new_opts))
        new_opts.insert(
            done_idx,
            {
                "name": "In Review",
                "color": "YELLOW",
                "description": "Awaiting Code Owner / lead review",
            },
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
                    options { id name }
                  }
                }
              }
            }
            """,
            "variables": {"fieldId": field["id"], "options": new_opts},
        }
    )
    opts = result["data"]["updateProjectV2Field"]["projectV2Field"]["options"]
    print("After:", [o["name"] for o in opts])


def update_issues() -> None:
    seed = []
    for n in sorted(ISSUES):
        item = ISSUES[n]
        print(f"Updating #{n} ...")
        tmp = Path(__file__).with_name(f"_issue_{n}_body.md")
        tmp.write_text(item["body"], encoding="utf-8")
        # gh api accepts raw body via input json
        payload = {"title": item["title"], "body": item["body"]}
        body_file = Path(__file__).with_name(f"_issue_{n}.json")
        body_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        run(
            [
                "gh",
                "api",
                "-X",
                "PATCH",
                f"repos/{REPO}/issues/{n}",
                "--input",
                str(body_file),
            ]
        )
        seed.append(
            {
                "number": n,
                "title": item["title"],
                "body": item["body"],
            }
        )
        tmp.unlink(missing_ok=True)
        body_file.unlink(missing_ok=True)

    # refresh local github_issues.json (titles+bodies only, keep labels from old if present)
    old_path = ROOT / "scripts" / "github_issues.json"
    old = json.loads(old_path.read_text(encoding="utf-8")) if old_path.exists() else []
    by_title = {x["title"]: x for x in old}
    out = []
    for n in sorted(ISSUES):
        title = ISSUES[n]["title"]
        prev = by_title.get(title, {})
        out.append(
            {
                "title": title,
                "labels": prev.get("labels", []),
                "body": ISSUES[n]["body"],
            }
        )
    old_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Wrote scripts/github_issues.json")


def main() -> int:
    load_token()
    print("=== Rename Status option ===")
    rename_status_option()
    print("=== Update issue bodies ===")
    update_issues()
    # spot check
    sample = json.loads(
        run(["gh", "api", f"repos/{REPO}/issues/16", "-q", ".body"])
        if False
        else run(["gh", "api", f"repos/{REPO}/issues/16"])
    )
    print("Sample #16 body starts:\n", sample.get("body", "")[:200].replace("\n", " | "))
    print("Done. Issues:", f"https://github.com/{REPO}/issues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
