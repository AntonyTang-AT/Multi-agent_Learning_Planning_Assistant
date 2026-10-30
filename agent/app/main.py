"""Agent FastAPI 入口 · 默认端口 8001。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, invoke
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Multi-agent Learning Planning Kernel",
    version=settings.agent_version,
    description="唯一智能内核：intent 路由 + Worker；LLM Key 仅在本服务。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(invoke.router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "agent",
        "version": settings.agent_version,
        "docs": "/docs",
        "health": "/health",
        "invoke": "/agent/v1/invoke",
    }
