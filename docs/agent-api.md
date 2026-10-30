# 多智能体 I/O API（3 号维护）

> Base：`http://localhost:8001`  
> 主入口：`POST /agent/v1/invoke`  
> 完整字段说明见 [技术路线与方案 · Agent I/O](./技术路线与方案.md#agent-io)  
> 样例：`agent/examples/`

## 调用约定

- 调用方仅为 **backend**（推荐）。  
- 所有智能能力通过 `intent` 区分。  
- 内部 Agent / LLM / SymPy **不对调用方暴露**。

## intent（MVP）

| intent | 说明 |
|---|---|
| `create_plan` | 生成计划草案并审计 |
| `arbitrate` | 用户裁决后重排/确认 |
| `generate_question` | 出题 |
| `verify_answer` | 校验 |
| `record_trace` | 轨迹侧轻量更新建议 |
| `challenge` | 结构化质疑 |
| `metacognitive_feedback` | 元认知卡片 |
| `proactive_intervention` | 主动干预卡片 |

## status

`ok` | `conflict` | `doubt` | `failed` | `abstain` | `need_user`

## 健康检查

`GET /health` → `{ "status": "up", "version": "0.1.0" }`

## 示例

见 `agent/examples/create_plan_final_review.json` 等。
