from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


APP_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = APP_ROOT.parent


class Settings(BaseSettings):
    app_name: str = "Crypto Bot Console"
    api_prefix: str = "/api"
    cors_origins: str = "http://127.0.0.1:5175,http://localhost:5175"
    freqtrade_dir: Path = WORKSPACE_ROOT / "freqtrade-agent"
    state_path: Path = APP_ROOT / "storage" / "state.json"
    live_env_path: Path = WORKSPACE_ROOT / "freqtrade-agent" / ".env.live.local"
    command_timeout_seconds: int = 900

    model_config = SettingsConfigDict(env_prefix="CRYPTO_CONSOLE_", env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
