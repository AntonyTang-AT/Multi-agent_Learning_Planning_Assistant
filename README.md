# 多智能体学习计划助手（高数 / 大物）

面向大学生 **期末复习** 与 **跟课补漏** 的 AI+学习生活项目。  
采用「传统 Web 学习站 + 独立多智能体智能内核」架构：前端与后端负责界面与数据存取，**全部 AI 能力封装在 `agent/` 服务中**，对外只保留稳定的输入 / 输出接口。

仓库地址：<https://github.com/AntonyTang-AT/Multi-agent_Learning_Planning_Assistant>

---

## 一句话创新

别人的多 Agent 在分工生成；我们的多 Agent 在分工**质疑、校验和协商**。  
计划冲突与不可靠答案会显式暴露，由用户裁决，系统不偷偷改计划、不强行给错答。

---

## 目录结构

```text
├── frontend/     # Web 前端（React + Vite + TS + Ant Design）
├── backend/      # 传统业务后端（FastAPI + SQLite，AI 仅转发）
├── agent/        # 多智能体智能内核（唯一调用 LLM / 校验处）
├── data/         # 高数·大物结构化资料包
├── docs/         # 方案、分工、技术路线、接口与任务计划
├── poster/       # A2 海报
├── pitch/        # PPT、路演稿、个人贡献备忘
└── scripts/      # 可选一键启动脚本
```

更细说明见 [`docs/项目文件结构.md`](docs/项目文件结构.md)。

---

## 已锁定技术栈

| 层级 | 选型 |
|---|---|
| 前端 | React 18 + Vite + TypeScript + Ant Design 5 + React Router + Axios + Zustand |
| 后端 | FastAPI + SQLAlchemy 2 + SQLite + Pydantic v2 + httpx |
| 智能内核 | FastAPI + intent 路由 + Worker 模块 + DeepSeek + SymPy（不强制 CrewAI） |
| 资料 | UTF-8 JSON + 校验脚本 |
| 本地端口 | 前端 `5173` · 后端 `8000` · Agent `8001` |

---

## 角色与文档入口

| 角色 | 文档 |
|---|---|
| 总方案 | [`docs/学习计划多智能体系统·形式化整体方案.md`](docs/学习计划多智能体系统·形式化整体方案.md) |
| 分工边界 | [`docs/五人分工与细化落地说明.md`](docs/五人分工与细化落地说明.md) |
| 逐日任务 | [`docs/五人详细任务计划.md`](docs/五人详细任务计划.md) |
| 技术路线 | [`docs/技术路线与方案.md`](docs/技术路线与方案.md) |
| 分人职责 | [`docs/roles/`](docs/roles/) |
| 业务 API | [`docs/api.md`](docs/api.md) |
| Agent I/O | [`docs/agent-api.md`](docs/agent-api.md) |

---

## 任务看板（Issue + Project）

- Issues：https://github.com/AntonyTang-AT/Multi-agent_Learning_Planning_Assistant/issues
- Project：https://github.com/users/AntonyTang-AT/projects/4
- 标签：`role:*`（前端/后端/agent/资料/答辩/闸门）、`phase:pre-12|post-12|gate`、`priority:P0|P1`
- 接取方式：在 Issue 点 **Assignees** 认领自己，并在 Project 把 **Status** 改为 `In Progress`；完成后改为 `Done` 并关闭 Issue

## 本地开发（骨架阶段）

当前仓库以**目录骨架 + 文档 + 样例资料**为主，三端工程将按任务计划逐步初始化。

1. 克隆本仓库  
2. 复制 `.env.example` 为 `.env`，填入本地密钥（**不要提交 `.env`**）  
3. 校验样例资料：

```bash
python data/scripts/validate_schema.py
```

4. 后续分别在 `frontend/`、`backend/`、`agent/` 按各自 README 启动。

---

## 安全说明

- `.env` 已写入 `.gitignore`，禁止把 GitHub Token、LLM Key 提交进仓库。  
- 若 Token 曾在聊天、截图或公开场合出现，请立刻到 GitHub → Settings → Developer settings 中**撤销并重新生成**。

---

## 许可证与资料合规

课程答辩学习使用。教材 / 真题等资料仅作结构化摘录与元数据整理，详见 `data/README.md`。合成演示数据须标注 `synthetic`。
