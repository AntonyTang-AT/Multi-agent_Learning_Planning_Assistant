# 后端业务 API（2 号维护）

> Base：`http://localhost:8000`  
> 错误体：`{ "code": string, "message": string, "detail"?: any }`  
> 详细技术约定见 [技术路线与方案](./技术路线与方案.md)

## 健康检查

`GET /api/health` → `{ "db": "up", "agent": "up"|"down" }`

## 会话

`POST /api/session` → `{ "user_id": "..." }`

## 资料与题目

- `GET /api/materials?subject=&chapter=&scenario_tag=`
- `GET /api/questions?subject=&knowledge_id=&scenario_tag=&exam_hot=`

## 计划

- `GET /api/plans/current`
- `PUT /api/plans/current` — 保存用户确认后的计划快照

## 作答

`POST /api/attempts` — body 含 `question_id`, `answer`, `error_tag?`, `duration_ms?`

## 黑板

- `GET /api/blackboard`
- `POST /api/blackboard/{id}/resolve` — `{ "action": "...", "note"?: "..." }`

## AI 网关（仅转发）

`POST /api/ai/{intent}`  

Body 对齐 Agent 请求子集；响应为 Agent 响应，并已落库。  

**联调必读（3 号已冻结）：**

- [`docs/前后端联调接口说明.md`](./前后端联调接口说明.md) — 网关职责、错误码、落库字段  
- [`docs/agent-api.md`](./agent-api.md) — intent / 请求响应合同  
- [`agent/examples/`](../agent/examples/) — 可拷贝 JSON  

`intent` 白名单与字段以 `agent-api.md` 为准；网关禁止写智能分支。

## 演示

`POST /api/demo/time-jump` — `{ "days": 2 }`

---

（实现时以 OpenAPI `/docs` 为准，本文件保持人读摘要同步。）
