from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.core.config import get_settings
from app.schemas import (
    AirdropAssistRequest,
    AirdropProjectRequest,
    AirdropRefreshRequest,
    AirdropTaskUpdateRequest,
    AirdropWalletRequest,
    BotActionRequest,
    ExchangeCredentialsRequest,
    JournalRequest,
    LiveOrderCancelRequest,
    LiveOrderRequest,
    LiveStartRequest,
    RiskRulesRequest,
    StrategyDraftRequest,
    WatchlistRequest,
)
from app.services.airdrops import assist_airdrop, create_airdrop_project, get_airdrop_dashboard, refresh_airdrop_sources, update_airdrop_task, upsert_airdrop_wallet
from app.services.freqtrade import (
    BOT_DEFS,
    bot_card,
    derived_alerts,
    derived_signals,
    list_backtests,
    list_bots,
    portfolio_snapshot,
    schedule_action,
    schedule_live_action,
    safety_audit,
    tail_logs,
)
from app.services.live_accounts import assert_live_start_allowed, cancel_live_order, connect_exchange, fetch_exchange_orders, list_live_orders, live_status, place_live_order, preview_live_order, refresh_live_account, write_live_config
from app.services.state import add_journal_entry, create_strategy_draft, read_state, write_state

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "single_user_live_connection_ready"}


@router.get("/settings")
def settings() -> dict:
    cfg = get_settings()
    return {
        "app_name": cfg.app_name,
        "freqtrade_dir": str(cfg.freqtrade_dir),
        "state_path": str(cfg.state_path),
        "cors_origins": cfg.cors_origin_list,
    }


@router.get("/overview")
def overview() -> dict:
    state = read_state()
    bots = list_bots()
    backtests = list_backtests()
    okx = next((item for item in bots if item["id"] == "okx_spot_dryrun"), None)
    last_okx_backtest = next((item for item in backtests if item["exchange"] == "okx"), None)
    feature_matrix = [
        {"name": "统一 Bot 控制台", "status": "ready"},
        {"name": "OKX dry-run 启停", "status": "ready"},
        {"name": "历史回测读取", "status": "ready"},
        {"name": "策略规则实验室", "status": "ready"},
        {"name": "本地风控阈值", "status": "ready"},
        {"name": "组合与持仓视图", "status": "ready"},
        {"name": "Grid/DCA/信号模板", "status": "ready"},
        {"name": "本地信号中心", "status": "ready"},
        {"name": "告警与复盘", "status": "ready"},
        {"name": "日志与任务队列", "status": "ready"},
        {"name": "路径与状态设置", "status": "ready"},
        {"name": "实盘安全硬锁", "status": "ready"},
        {"name": "OKX/Binance 真实账号接入", "status": "ready"},
        {"name": "实盘配置生成与预检", "status": "ready"},
        {"name": "实盘订单查询与撤单", "status": "ready"},
        {"name": "空投项目实时源", "status": "ready"},
        {"name": "空投任务与成本台账", "status": "ready"},
        {"name": "多账号", "status": "out_of_scope"},
    ]
    airdrops = get_airdrop_dashboard()
    return {
        "profile": state["profile"],
        "safety": {
            "live_trading": "preflight_required",
            "withdraw_permission": "forbidden",
            "futures_margin_short": "forbidden",
            "single_user": True,
        },
        "primary_bot": okx,
        "bots": bots,
        "risk": state["risk"],
        "backtests": backtests[:6],
        "last_okx_backtest": last_okx_backtest,
        "watchlist": state["watchlist"],
        "portfolio": portfolio_snapshot(),
        "signals": derived_signals(),
        "alerts": derived_alerts(state["risk"]),
        "live": live_status(),
        "airdrops": {
            "last_refresh_at": airdrops["last_refresh_at"],
            "metrics": airdrops["metrics"],
        },
        "feature_matrix": feature_matrix,
        "tasks": state.get("tasks", [])[:8],
    }


@router.get("/bots")
def get_bots() -> list[dict]:
    return list_bots()


@router.get("/bots/{bot_id}")
def get_bot(bot_id: str) -> dict:
    if bot_id not in BOT_DEFS:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot_card(bot_id)


@router.get("/bots/{bot_id}/safety")
def get_bot_safety(bot_id: str) -> dict:
    if bot_id not in BOT_DEFS:
        raise HTTPException(status_code=404, detail="Bot not found")
    return safety_audit(bot_id)


@router.get("/bots/{bot_id}/logs")
def get_bot_logs(bot_id: str, lines: int = 200) -> dict:
    if bot_id not in BOT_DEFS:
        raise HTTPException(status_code=404, detail="Bot not found")
    return tail_logs(bot_id, lines=max(20, min(lines, 500)))


@router.post("/bots/{bot_id}/actions")
def post_bot_action(bot_id: str, payload: BotActionRequest) -> dict:
    if bot_id not in BOT_DEFS:
        raise HTTPException(status_code=404, detail="Bot not found")
    try:
        return schedule_action(payload.action, bot_id=bot_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/actions")
def post_global_action(payload: BotActionRequest) -> dict:
    try:
        return schedule_action(payload.action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/live/status")
def get_live_status() -> dict:
    return live_status()


@router.post("/live/accounts/connect")
def post_live_account_connect(payload: ExchangeCredentialsRequest) -> dict:
    try:
        return connect_exchange(payload.model_dump())
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[-1000:] if exc.response is not None else str(exc)
        raise HTTPException(status_code=400, detail=f"Exchange rejected the connection test: {detail}") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/live/accounts/{exchange}/refresh")
def post_live_account_refresh(exchange: str) -> dict:
    try:
        return refresh_live_account(exchange)
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[-1000:] if exc.response is not None else str(exc)
        raise HTTPException(status_code=400, detail=f"Exchange rejected the refresh: {detail}") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/live/configs/{exchange}")
def post_live_config(exchange: str) -> dict:
    if exchange not in {"okx", "binance"}:
        raise HTTPException(status_code=404, detail="Unsupported exchange")
    path = write_live_config(exchange, local=False)
    return {"exchange": exchange, "path": str(path), "local": False}


@router.get("/live/preflight")
def get_live_preflight() -> dict:
    return live_status()["preflight"]


@router.post("/live/start")
def post_live_start(payload: LiveStartRequest) -> dict:
    try:
        preflight = assert_live_start_allowed(payload.exchange, payload.ack)
        task = schedule_live_action(payload.exchange)
        return {"task": task, "preflight": preflight}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/live/orders/preview")
def post_live_order_preview(payload: LiveOrderRequest) -> dict:
    return preview_live_order(payload.model_dump())


@router.post("/live/orders")
def post_live_order(payload: LiveOrderRequest) -> dict:
    try:
        return place_live_order(payload.model_dump())
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[-1000:] if exc.response is not None else str(exc)
        raise HTTPException(status_code=400, detail=f"Exchange rejected the order: {detail}") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/live/orders")
def get_live_orders() -> list[dict]:
    return list_live_orders()


@router.get("/live/orders/open")
def get_live_open_orders(exchange: str, pair: Optional[str] = None) -> dict:
    try:
        return fetch_exchange_orders(exchange, "open", pair=pair)
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[-1000:] if exc.response is not None else str(exc)
        raise HTTPException(status_code=400, detail=f"Exchange rejected the open-order query: {detail}") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/live/orders/history")
def get_live_order_history(exchange: str, pair: Optional[str] = None) -> dict:
    try:
        return fetch_exchange_orders(exchange, "history", pair=pair)
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[-1000:] if exc.response is not None else str(exc)
        raise HTTPException(status_code=400, detail=f"Exchange rejected the order-history query: {detail}") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/live/orders/cancel")
def post_live_order_cancel(payload: LiveOrderCancelRequest) -> dict:
    try:
        return cancel_live_order(payload.model_dump())
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[-1000:] if exc.response is not None else str(exc)
        raise HTTPException(status_code=400, detail=f"Exchange rejected the cancel request: {detail}") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/tasks")
def get_tasks() -> list[dict]:
    return read_state().get("tasks", [])


@router.get("/airdrops")
def get_airdrops() -> dict:
    return get_airdrop_dashboard()


@router.post("/airdrops/refresh")
def post_airdrop_refresh(payload: AirdropRefreshRequest) -> dict:
    try:
        return refresh_airdrop_sources(project_id=payload.project_id, live=payload.live)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/airdrops/{project_id}/assist")
def post_airdrop_assist(project_id: str, payload: AirdropAssistRequest) -> dict:
    try:
        return assist_airdrop(project_id, live=payload.live)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/airdrops/projects")
def post_airdrop_project(payload: AirdropProjectRequest) -> dict:
    try:
        return create_airdrop_project(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/airdrops/projects/{project_id}/tasks/{task_id}")
def put_airdrop_task(project_id: str, task_id: str, payload: AirdropTaskUpdateRequest) -> dict:
    try:
        return update_airdrop_task(project_id, task_id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/airdrops/wallets")
def post_airdrop_wallet(payload: AirdropWalletRequest) -> dict:
    return upsert_airdrop_wallet(payload.model_dump())


@router.get("/backtests")
def get_backtests() -> list[dict]:
    return list_backtests()


@router.get("/portfolio")
def get_portfolio() -> dict:
    return portfolio_snapshot()


@router.get("/signals")
def get_signals() -> list[dict]:
    return derived_signals()


@router.get("/alerts")
def get_alerts() -> list[dict]:
    state = read_state()
    return derived_alerts(state["risk"])


@router.get("/templates")
def get_templates() -> list[dict]:
    return read_state().get("bot_templates", [])


@router.post("/templates/{template_id}/clone")
def clone_template(template_id: str) -> dict:
    state = read_state()
    template = next((item for item in state.get("bot_templates", []) if item["id"] == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    payload = {
        "name": f"{template['name']} Draft",
        "timeframe": template["timeframe"],
        "pairs": template["pairs"],
        "entry_rules": [f"{template['type']} template: {key}={value}" for key, value in template.get("settings", {}).items()],
        "exit_rules": template.get("risk", []),
        "risk_notes": "Cloned from template. Dry-run/backtest required before use.",
    }
    return create_strategy_draft(payload)


@router.post("/backtests/run")
def run_backtest(exchange: str = "okx") -> dict:
    action = "backtest-okx" if exchange == "okx" else "backtest-binance"
    bot_id = "okx_spot_dryrun" if exchange == "okx" else "binance_spot_dryrun"
    try:
        return schedule_action(action, bot_id=bot_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/strategies")
def get_strategies() -> list[dict]:
    return read_state().get("strategy_drafts", [])


@router.post("/strategies")
def post_strategy(payload: StrategyDraftRequest) -> dict:
    return create_strategy_draft(payload.model_dump())


@router.get("/risk")
def get_risk() -> dict:
    return read_state()["risk"]


@router.put("/risk")
def put_risk(payload: RiskRulesRequest) -> dict:
    state = read_state()
    state["risk"].update(payload.model_dump())
    write_state(state)
    return state["risk"]


@router.get("/market/watchlist")
def get_watchlist() -> list[dict]:
    return read_state().get("watchlist", [])


@router.put("/market/watchlist")
def put_watchlist(payload: WatchlistRequest) -> list[dict]:
    state = read_state()
    state["watchlist"] = payload.watchlist
    write_state(state)
    return state["watchlist"]


@router.get("/journal")
def get_journal() -> list[dict]:
    return read_state().get("journal", [])


@router.post("/journal")
def post_journal(payload: JournalRequest) -> dict:
    return add_journal_entry(payload.model_dump())
