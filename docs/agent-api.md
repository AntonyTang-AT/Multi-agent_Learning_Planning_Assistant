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
| `create_plan` | 生成计划草案并审计；冲突时返回 `conflict` + 黑板 + 三选项；支持 `demo.force_conflict`；若 `input.error_tag` 有值则按错因策略表插入差异化任务，并可能附带 `challenge`/`intervention` 黑板条目 |
| `arbitrate` | 用户裁决后重排/确认（`input.option_id` + `input.plan`） |
| `generate_question` | 出题；优先 `resource_payload.sample_questions`；必须过 Verifier；失败重试后 `abstain`；支持 `demo.force_verify_fail` |
| `verify_answer` | 校验；`output.verdict` + `audit_trail`；失败返回 `abstain`（不硬给错答） |
| `record_trace` | 轨迹侧轻量更新建议 |
| `challenge` | 结构化质疑 |
| `metacognitive_feedback` | 元认知卡片 |
| `proactive_intervention` | 主动干预卡片 |
| `echo` | **调试用回声**（A1；联调 schema，正式业务勿依赖） |

未知 `intent`：HTTP `400`，`detail.code = unknown_intent`，并返回 `supported_intents` 列表。

## status

`ok` | `conflict` | `doubt` | `failed` | `abstain` | `need_user`

## 健康检查

`GET /health` → `{ "status": "up", "version": "0.1.0" }`

## 示例

见 `agent/examples/create_plan_final_review.json` 等。
