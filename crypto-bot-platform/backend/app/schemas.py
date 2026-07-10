from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class BotActionRequest(BaseModel):
    action: str = Field(min_length=2, max_length=40)
    ack: str = ""


class StrategyDraftRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    timeframe: str = "15m"
    pairs: list[str] = Field(default_factory=list)
    entry_rules: list[str] = Field(default_factory=list)
    exit_rules: list[str] = Field(default_factory=list)
    risk_notes: str = ""


class RiskRulesRequest(BaseModel):
    max_open_trades: int = Field(ge=1, le=3)
    stake_amount: float = Field(gt=0, le=50)
    daily_loss_limit_pct: float = Field(gt=0, le=5)
    pause_drawdown_pct: float = Field(gt=0, le=10)
    hard_stop_drawdown_pct: float = Field(gt=0, le=20)
    max_consecutive_losses: int = Field(ge=1, le=3)
    allowed_pairs: list[str]


class WatchlistRequest(BaseModel):
    watchlist: list[dict]


class JournalRequest(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    body: str = Field(min_length=2, max_length=2000)
    tags: list[str] = Field(default_factory=list)


class ExchangeCredentialsRequest(BaseModel):
    exchange: str = Field(pattern="^(okx|binance)$")
    api_key: str = Field(min_length=4, max_length=256)
    api_secret: str = Field(min_length=4, max_length=512)
    passphrase: str = Field(default="", max_length=256)
    label: str = Field(default="", max_length=80)
    test_connection: bool = True
    save_to_env: bool = False
    generate_live_config: bool = True


class LiveStartRequest(BaseModel):
    exchange: str = Field(pattern="^(okx|binance)$")
    ack: str = Field(min_length=2, max_length=80)


class AirdropRefreshRequest(BaseModel):
    project_id: Optional[str] = None
    live: bool = True


class AirdropAssistRequest(BaseModel):
    live: bool = True


class AirdropProjectRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    chain: str = Field(default="Unknown", max_length=60)
    category: str = Field(default="Custom", max_length=80)
    official_url: str = Field(min_length=8, max_length=600)
    status: str = Field(default="watch", pattern="^(active|watch|paused|ended)$")
    priority: str = Field(default="medium", pattern="^(high|medium|low)$")
    stage: str = Field(default="monitor", max_length=60)
    risk_level: str = Field(default="medium", pattern="^(low|medium|high)$")
    cost_level: str = Field(default="unknown", max_length=40)
    notes: str = Field(default="", max_length=1000)


class AirdropTaskUpdateRequest(BaseModel):
    status: Optional[str] = Field(default=None, pattern="^(todo|done|blocked)$")
    evidence: str = Field(default="", max_length=1000)
    tx_hash: str = Field(default="", max_length=160)
    cost_usd: Optional[float] = Field(default=None, ge=0, le=100000)


class AirdropWalletRequest(BaseModel):
    id: Optional[str] = Field(default=None, max_length=80)
    label: str = Field(min_length=2, max_length=80)
    chains: list[str] = Field(default_factory=list)
    role: str = Field(default="airdrop tasks", max_length=120)
    status: str = Field(default="ready", max_length=40)
    notes: str = Field(default="", max_length=800)


class LiveOrderRequest(BaseModel):
    exchange: str = Field(pattern="^(okx|binance)$")
    pair: str = Field(pattern="^[A-Z0-9]+/[A-Z0-9]+$")
    side: str = Field(pattern="^(buy|sell)$")
    order_type: str = Field(default="limit", pattern="^(limit|market)$")
    quote_amount: float = Field(gt=0, le=10)
    price: Optional[float] = Field(default=None, gt=0)
    ack: str = Field(default="", max_length=120)


class LiveOrderCancelRequest(BaseModel):
    exchange: str = Field(pattern="^(okx|binance)$")
    pair: str = Field(pattern="^[A-Z0-9]+/[A-Z0-9]+$")
    order_id: Optional[str] = Field(default=None, max_length=120)
    client_order_id: Optional[str] = Field(default=None, max_length=120)
    ack: str = Field(min_length=2, max_length=120)
