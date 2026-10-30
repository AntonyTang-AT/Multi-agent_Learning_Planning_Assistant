# agent（3 号 · 多智能体智能内核）

**锁定栈**：FastAPI + intent 路由 + Worker + DeepSeek + SymPy（不强制 CrewAI）。

- 默认端口 **`8001`**
- API Key **只放本服务**（`agent/.env` 或仓库根 `.env` 的 `DEEPSEEK_API_KEY`）
- 职责：`docs/roles/03-多智能体.md` · 任务：`docs/五人详细任务计划.md`
- I/O：`docs/agent-api.md`、`docs/技术路线与方案.md`

## 当前进度

- [x] A1 `GET /health` + `POST /agent/v1/invoke` + `echo` + schema
- [x] A2 `create_plan` 规则审计冲突 + `user_options` + `arbitrate`
- [x] A3 `generate_question` / `verify_answer` + 校验失败弃答（`force_verify_fail`）
- [ ] A4 错因策略 + 黑板增强

## 启动

```bash
cd agent
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

浏览器打开：http://localhost:8001/docs

## 快速验收

```bash
# 健康检查
curl http://localhost:8001/health

# 回声
curl -X POST http://localhost:8001/agent/v1/invoke ^
  -H "Content-Type: application/json" ^
  -d "{\"request_id\":\"r1\",\"task_id\":\"t1\",\"intent\":\"echo\",\"input\":{\"hello\":\"world\"}}"
```

或跑测试：

```bash
cd agent
pytest -q
```

## 目录

```text
agent/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py
│   ├── api/                 # health / invoke
│   ├── schemas/             # request / response
│   ├── orchestrator/        # intent 路由
│   ├── workers/             # echo（A1）；后续 planner/verifier…
│   ├── rules/ blackboard/ llm/ demos/
├── examples/                # 联调 JSON
├── tests/
├── requirements.txt
└── .env.example
```
