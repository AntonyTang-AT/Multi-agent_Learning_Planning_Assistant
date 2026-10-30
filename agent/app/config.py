"""Agent 服务配置。优先读 agent/.env，其次仓库根目录 .env。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

AGENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AGENT_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            str(REPO_ROOT / ".env"),
            str(AGENT_ROOT / ".env"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepseek_api_key: str = ""
    model_name: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com"
    agent_host: str = "0.0.0.0"
    agent_port: int = 8001
    agent_version: str = "0.1.0"
    log_sensitive: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
