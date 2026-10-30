# backend（2 号）

**锁定栈**：FastAPI + SQLAlchemy 2 + SQLite + Pydantic v2 + httpx · 传统 Web API，AI 仅转发。

- 默认端口 `8000` · `AGENT_BASE_URL=http://localhost:8001` · **不放 LLM Key**
- 职责：`docs/roles/02-后端.md` · 任务：`docs/五人详细任务计划.md`
- 接口：`docs/api.md`

```bash
# 示例（工程就绪后）
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
