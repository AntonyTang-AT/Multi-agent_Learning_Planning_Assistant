# 多智能体 I/O API（3 号维护 · 合同正文）

> Base：`http://localhost:8001`  
> 主入口：`POST /agent/v1/invoke`  
> 健康检查：`GET /health`  
> 样例目录：[`agent/examples/`](../agent/examples/)  
> 前后端怎么接：[`docs/前后端联调接口说明.md`](./前后端联调接口说明.md)  
> 背景：[`技术路线与方案 · Agent I/O`](./技术路线与方案.md#agent-io)

**调用方**：仅 **backend**（推荐）。前端经 `POST /api/ai/{intent}` 间接收到同等响应形状。

---

## 1. 健康检查

`GET /health`

```json
{ "status": "up", "version": "0.1.0" }
```

---

## 2. 统一请求体 `AgentRequest`

`POST /agent/v1/invoke`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `request_id` | string | 是 | 调用方生成，原样回传 |
| `task_id` | string | 是 | 任务关联 ID |
| `scenario` | `final_review` \| `catch_up` | 否 | 默认 `final_review` |
| `intent` | string | 是 | 见下表；未知 intent → HTTP 400 |
| `user_profile` | object | 否 | `user_id` + `constraints.hard/soft` |
| `input` | object | 否 | **按 intent 解释** 的业务输入 |
| `resource_refs` | array | 否 | `{type,id,label?}` 知识点/资源引用 |
| `resource_payload` | object | 否 | 如 `sample_questions[]` |
| `trace_snapshot` | object | 否 | `recent_attempts` / `load_signals` 等 |
| `demo` | object | 否 | 演示开关 |

### `demo` 开关

| 字段 | 说明 |
|---|---|
| `force_conflict` | 强制计划审计冲突（答辩必演） |
| `force_verify_fail` | 强制校验失败 → 弃答 |
| `time_jump_days` | 时间跳跃天数（触发主动干预） |

### `constraints.hard` 常用写法

- `daily_minutes<=45`
- `exam_date=2026-01-10`
- `subject=math`

---

## 3. 统一响应体 `AgentResponse`

| 字段 | 类型 | 说明 |
|---|---|---|
| `request_id` / `task_id` | string | 回传 |
| `status` | enum | 见下节 |
| `message` | string | 人可读摘要（可直接 Toast） |
| `output` | object | **按 intent 变化** |
| `blackboard_entries` | array | 黑板条目 |
| `user_options` | array | `{id,label}` 用户可选项 |
| `evidence_refs` | array | 证据引用（可空） |
| `requires_approval` | bool | 是否需用户确认后落库 |
| `meta` | object | `agent_version`, `latency_ms` |

### `status`

`ok` | `conflict` | `doubt` | `failed` | `abstain` | `need_user`

### 黑板条目

```json
{
  "entry_id": "bb_xxx",
  "type": "conflict|challenge|intervention",
  "summary": "...",
  "severity": "high|medium|low",
  "evidence_refs": [],
  "status": "open"
}
```

### 未知 intent

HTTP `400`：

```json
{
  "detail": {
    "code": "unknown_intent",
    "message": "不支持的 intent: xxx",
    "supported_intents": ["arbitrate", "challenge", "..."]
  }
}
```

---

## 4. intent 一览

| intent | 状态 | 说明 |
|---|---|---|
| `create_plan` | ✅ | 计划草案 + 规则审计；可冲突；可错因插入 |
| `arbitrate` | ✅ | 用户选项后重排 |
| `generate_question` | ✅ | 出题 + 校验门禁；失败弃答 |
| `verify_answer` | ✅ | 答案校验；失败弃答 |
| `challenge` | ✅ | 缺假设结构化质疑 |
| `metacognitive_feedback` | ✅ | 元认知卡片 |
| `proactive_intervention` | ✅ | 主动干预卡片 |
| `echo` | ✅ 调试 | 回声；正式业务勿用 |
| `record_trace` | ❌ 占位 | 返回 `status=failed`（尚未实现） |

---

## 5. 各 intent 的 `input` / `output`

### 5.1 `create_plan`

**input 常用**

| 字段 | 说明 |
|---|---|
| `goal` | 目标文案 |
| `days_left` | 天数 |
| `error_tag` | 错因：`limit_misuse` / `symbol_error` / `undefined_assumption` / `conceptual_gap` |

**output**

- 成功：`{ "plan": { "tasks": [...], ... }, "error_strategy"?: {...} }`
- 冲突：同上 + `audit_issues`；顶层 `user_options` 三选项：  
  `extend_time` | `reduce_depth` | `adjust_goal`

**样例**：`create_plan_final_review.json`（冲突）、`create_plan_ok.json`、`create_plan_error_*.json`

### 5.2 `arbitrate`

**input**

| 字段 | 必填 | 说明 |
|---|---|---|
| `option_id` | 是 | 与 `user_options.id` 对应 |
| `plan` | 是 | 上一轮计划对象（或 `output.plan`） |

**output**：`{ "plan": { ... , "arbitration": {...} } }`

**样例**：`arbitrate_extend_time.json`

### 5.3 `generate_question`

**input / payload**：优先 `resource_payload.sample_questions[]`；否则模板。

**output**

- 成功：`{ "question": {...}, "verdict": "passed", "audit_trail": [] }`
- 弃答：`status=abstain`，`output.question=null`，`hint_mode=true`

**样例**：`generate_question_ok.json`、`generate_question_force_abstain.json`

### 5.4 `verify_answer`

**input**

| 字段 | 说明 |
|---|---|
| `answer` | 待校验答案 |
| `verify_hint` | `{ "expr": "limit(sin(x)/x, x, 0)", "expected": "1" }` |
| `question` | 可选，内含 answer/verify_hint |

**output**：`verdict` + `audit_trail` + `diff?`；失败时 `status=abstain` 且 `hint_mode=true`

**样例**：`verify_answer_ok.json`、`verify_answer_force_fail.json`

### 5.5 `challenge`

**input**：`question`（含 `assumptions`；空则质疑）或 `force_challenge`

**output**：`card`（structured_challenge）+ 黑板 `challenge`；`status=need_user`

**样例**：`challenge_missing_assumption.json`

### 5.6 `metacognitive_feedback`

**input**：`topic?`、`error_tag?`

**output**：`card.type = metacognitive`；`status=ok`

**样例**：`metacognitive_feedback.json`

### 5.7 `proactive_intervention`

**触发**：`demo.time_jump_days >= 2` 或 `trace_snapshot.load_signals.overload`

**output**：`card` + 黑板 `intervention`；`status=need_user`

**样例**：`proactive_intervention_time_jump.json`

### 5.8 `echo`（调试）

**output**：回显 `input` 等；`status=ok`

---

## 6. examples 索引

| 文件 | 场景 |
|---|---|
| `echo.json` | 调试回声 |
| `create_plan_final_review.json` | 强制冲突三选项 |
| `create_plan_ok.json` | 正常通过 |
| `create_plan_error_limit_misuse.json` | 错因：回顾概念 |
| `create_plan_error_symbol_error.json` | 错因：变式练习 |
| `arbitrate_extend_time.json` | 延长时间裁决 |
| `verify_answer_ok.json` / `verify_answer_force_fail.json` | 校验通过 / 弃答 |
| `generate_question_ok.json` / `generate_question_force_abstain.json` | 出题 / 弃答 |
| `challenge_missing_assumption.json` | 缺假设质疑 |
| `metacognitive_feedback.json` | 元认知 |
| `proactive_intervention_time_jump.json` | 时间跳跃干预 |

> 部分文件含 `request` + `response_example`/`notes` 包装；**HTTP 只 POST `request` 对象**。

---

## 7. 本地验证

```bash
cd agent
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

pytest -q
python -m app.demos.run_three_must --with-enhancements
```

OpenAPI：http://localhost:8001/docs
