# agent（3 号）

**锁定栈**：FastAPI + intent 路由 + Worker + DeepSeek + SymPy（不强制 CrewAI）。

- 默认端口 `8001` · API Key 只放本目录 `.env`
- 职责：`docs/roles/03-多智能体.md` · 任务：`docs/五人详细任务计划.md`
- I/O：`docs/agent-api.md`、`docs/技术路线与方案.md`

```bash
# 示例（工程就绪后）
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```
