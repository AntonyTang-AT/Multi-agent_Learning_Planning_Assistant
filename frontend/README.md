# frontend（1 号）

**锁定栈**：React 18 + Vite + TypeScript + Ant Design 5 + React Router 6 + Axios + Zustand

- 只请求 `backend`（默认 `http://localhost:8000`）
- 职责：`docs/roles/01-前端.md` · 任务：`docs/五人详细任务计划.md`

```bash
npm create vite@latest . -- --template react-ts
npm i antd react-router-dom axios zustand
npm run dev
```

`.env.example`：

```env
VITE_API_BASE=http://localhost:8000
VITE_USE_MOCK=true
```

