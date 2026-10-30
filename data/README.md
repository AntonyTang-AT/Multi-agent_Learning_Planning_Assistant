# data（4 号）

高数 / 大物宽覆盖资料包。服务场景：`final_review`（期末复习）、`catch_up`（跟课补漏）。

- 职责与验收：`docs/roles/04-资料整理.md`
- 导入方：`backend` 的 import 脚本
- 版权：仅答辩学习使用；摘录与改编范围在此补充；合成数据放 `synthetic/` 并标注

## 目录

- `taxonomy/` — 大纲与知识点
- `materials/` — 课件/教材元数据
- `questions/` — 习题例题
- `exams/` — 真题向
- `catch_up/` · `final_review/` — 场景聚合（可选）
- `scripts/validate_schema.py` — 校验

## 导入前检查

```bash
python scripts/validate_schema.py
```
