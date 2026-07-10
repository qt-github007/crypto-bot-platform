from __future__ import annotations

import json
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from app.core.config import get_settings

_LOCK = threading.Lock()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _default_airdrop_workspace() -> dict[str, Any]:
    return {
        "settings": {
            "refresh_interval_minutes": 30,
            "source_timeout_seconds": 6,
            "safety_boundary": "manual wallet signing only; no seed phrases, no private keys, no KYC bypass, no sybil automation",
        },
        "last_refresh_at": None,
        "wallets": [
            {
                "id": "wallet-watch-1",
                "label": "观察钱包",
                "chains": ["EVM", "Solana"],
                "role": "低额度交互与任务记录",
                "status": "ready",
                "notes": "只放小额 gas；不要在平台保存助记词或私钥。",
            }
        ],
        "projects": [
            {
                "id": "metamask-rewards",
                "name": "MetaMask Rewards",
                "chain": "Multi-chain",
                "category": "钱包 / Rewards",
                "status": "active",
                "priority": "high",
                "stage": "rewards",
                "risk_level": "medium",
                "cost_level": "low",
                "official_url": "https://metamask.io/rewards/",
                "notes": "适合把本来就要做的钱包交互记录下来；不要为了积分硬刷交易量。",
                "sources": [
                    {"label": "Rewards", "url": "https://metamask.io/rewards/", "kind": "official"},
                    {
                        "label": "How to participate",
                        "url": "https://support.metamask.io/manage-crypto/metamask-rewards/how-to-participate-in-rewards/",
                        "kind": "support",
                    },
                ],
                "tasks": [
                    {"id": "mm-open", "title": "打开官方 Rewards 页面核对当前任务", "status": "todo", "kind": "research", "evidence": "", "tx_hash": "", "cost_usd": 0},
                    {"id": "mm-wallet", "title": "用低额度钱包完成一次真实需求交互", "status": "todo", "kind": "interaction", "evidence": "", "tx_hash": "", "cost_usd": 0},
                    {"id": "mm-review", "title": "记录 gas、手续费和积分变化", "status": "todo", "kind": "review", "evidence": "", "tx_hash": "", "cost_usd": 0},
                ],
                "source_results": [],
                "signals": [],
                "last_checked_at": None,
                "source_health": "not_checked",
            },
            {
                "id": "lighter-points",
                "name": "Lighter Points",
                "chain": "Ethereum L2",
                "category": "Perp DEX / Points",
                "status": "active",
                "priority": "medium",
                "stage": "points",
                "risk_level": "high",
                "cost_level": "medium",
                "official_url": "https://docs.lighter.xyz/points-program",
                "notes": "合约/永续相关风险高；只适合小仓或观察，禁止高杠杆冲积分。",
                "sources": [
                    {"label": "Points program", "url": "https://docs.lighter.xyz/points-program", "kind": "docs"},
                    {"label": "Retail points", "url": "https://docs.lighter.xyz/points-program/retail", "kind": "docs"},
                ],
                "tasks": [
                    {"id": "lighter-doc", "title": "阅读积分规则与反自成交说明", "status": "todo", "kind": "research", "evidence": "", "tx_hash": "", "cost_usd": 0},
                    {"id": "lighter-risk", "title": "设置单日最大亏损和最大手续费预算", "status": "todo", "kind": "risk", "evidence": "", "tx_hash": "", "cost_usd": 0},
                    {"id": "lighter-review", "title": "记录每次交易成本和积分变化", "status": "todo", "kind": "review", "evidence": "", "tx_hash": "", "cost_usd": 0},
                ],
                "source_results": [],
                "signals": [],
                "last_checked_at": None,
                "source_health": "not_checked",
            },
            {
                "id": "somnia-quests",
                "name": "Somnia Quests",
                "chain": "Somnia",
                "category": "Testnet / Quests",
                "status": "active",
                "priority": "medium",
                "stage": "quests",
                "risk_level": "medium",
                "cost_level": "low",
                "official_url": "https://quest.somnia.network/",
                "notes": "以任务和生态交互为主，适合低成本跟踪；资格规则可能随赛季变化。",
                "sources": [
                    {"label": "Quest", "url": "https://quest.somnia.network/", "kind": "official"},
                    {"label": "Airdrop policy", "url": "https://docs.somnia.network/concepts/miscellaneous/legal/airdrop-policy", "kind": "docs"},
                ],
                "tasks": [
                    {"id": "somnia-open", "title": "打开 Quest 页面核对当前任务", "status": "todo", "kind": "research", "evidence": "", "tx_hash": "", "cost_usd": 0},
                    {"id": "somnia-eco", "title": "挑 1 个生态项目做低成本真实交互", "status": "todo", "kind": "interaction", "evidence": "", "tx_hash": "", "cost_usd": 0},
                    {"id": "somnia-proof", "title": "保存任务截图或 tx hash", "status": "todo", "kind": "evidence", "evidence": "", "tx_hash": "", "cost_usd": 0},
                ],
                "source_results": [],
                "signals": [],
                "last_checked_at": None,
                "source_health": "not_checked",
            },
            {
                "id": "grass-rewards",
                "name": "Grass Rewards",
                "chain": "Solana",
                "category": "DePIN / Rewards",
                "status": "active",
                "priority": "medium",
                "stage": "points",
                "risk_level": "medium",
                "cost_level": "low",
                "official_url": "https://app.getgrass.io/",
                "notes": "低资金门槛，但涉及设备、网络和隐私；不要在主力网络环境裸跑。",
                "sources": [
                    {"label": "Official app", "url": "https://app.getgrass.io/", "kind": "official"},
                ],
                "tasks": [
                    {"id": "grass-setup", "title": "确认官方域名和设备隔离方案", "status": "todo", "kind": "safety", "evidence": "", "tx_hash": "", "cost_usd": 0},
                    {"id": "grass-run", "title": "记录节点运行时间和积分变化", "status": "todo", "kind": "review", "evidence": "", "tx_hash": "", "cost_usd": 0},
                    {"id": "grass-privacy", "title": "复查隐私和网络风险", "status": "todo", "kind": "risk", "evidence": "", "tx_hash": "", "cost_usd": 0},
                ],
                "source_results": [],
                "signals": [],
                "last_checked_at": None,
                "source_health": "not_checked",
            },
            {
                "id": "eclipse-season-watch",
                "name": "Eclipse Season Watch",
                "chain": "Eclipse",
                "category": "Ecosystem / Future season",
                "status": "watch",
                "priority": "low",
                "stage": "monitor",
                "risk_level": "medium",
                "cost_level": "low",
                "official_url": "https://www.eclipse.xyz/articles/everything-eclipse-ed-12",
                "notes": "已发 ES，但官方仍提到 future season 预留；适合关注生态活动而不是重仓刷。",
                "sources": [
                    {"label": "Everything Eclipse", "url": "https://www.eclipse.xyz/articles/everything-eclipse-ed-12", "kind": "official"},
                ],
                "tasks": [
                    {"id": "eclipse-monitor", "title": "刷新官方公告，确认是否出现新赛季", "status": "todo", "kind": "research", "evidence": "", "tx_hash": "", "cost_usd": 0},
                    {"id": "eclipse-eco", "title": "只记录有真实需求的生态交互", "status": "todo", "kind": "interaction", "evidence": "", "tx_hash": "", "cost_usd": 0},
                ],
                "source_results": [],
                "signals": [],
                "last_checked_at": None,
                "source_health": "not_checked",
            },
        ],
        "activity_log": [
            {
                "id": "airdrop-initial-note",
                "created_at": now(),
                "title": "空投工作区初始化",
                "body": "只记录官方源、任务、成本和证据；签名动作仍在钱包内手动确认。",
                "severity": "info",
            }
        ],
    }


def _default_state() -> dict[str, Any]:
    return {
        "version": 1,
        "created_at": now(),
        "updated_at": now(),
        "profile": {
            "owner": "local-single-user",
            "mode": "dry-run with live-connection readiness",
            "base_currency": "USDT",
            "paper_wallet": 1000,
            "product_target": "single-user exchange-connected trading console",
        },
        "risk": {
            "max_open_trades": 3,
            "stake_amount": 50,
            "daily_loss_limit_pct": 5,
            "pause_drawdown_pct": 10,
            "hard_stop_drawdown_pct": 20,
            "max_consecutive_losses": 3,
            "allowed_pairs": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
            "forbidden": ["live trading", "withdraw permission", "futures", "margin", "shorting", "leverage"],
        },
        "live_trading": {
            "enabled": False,
            "ack_required": "我确认这是实盘交易并愿意承担风险",
            "max_live_stake_amount": 10,
            "max_live_open_trades": 1,
            "allowed_exchanges": ["okx", "binance"],
            "last_preflight": None,
        },
        "live_accounts": {
            "okx": {
                "exchange": "okx",
                "label": "OKX",
                "status": "not_connected",
                "masked_api_key": "",
                "permissions": {},
                "balances": [],
                "last_checked_at": None,
                "saved_to_env": False,
                "config_path": "",
                "issues": [],
            },
            "binance": {
                "exchange": "binance",
                "label": "Binance",
                "status": "not_connected",
                "masked_api_key": "",
                "permissions": {},
                "balances": [],
                "last_checked_at": None,
                "saved_to_env": False,
                "config_path": "",
                "issues": [],
            },
        },
        "live_orders": [],
        "strategy_drafts": [
            {
                "id": "hybrid-safe-v1",
                "name": "Hybrid Safe v1",
                "status": "active",
                "timeframe": "15m",
                "pairs": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
                "entry_rules": [
                    "EMA20 above EMA50",
                    "RSI between 35 and 65",
                    "Volume above 30-candle mean",
                ],
                "exit_rules": ["Close below EMA50", "RSI above 75", "Stoploss -5%"],
                "risk_notes": "Dry-run only; prior backtests are negative, so live promotion is locked.",
                "created_at": now(),
            },
            {
                "id": "trend-filter-draft",
                "name": "Trend Filter Draft",
                "status": "draft",
                "timeframe": "15m + 1h filter",
                "pairs": ["BTC/USDT", "ETH/USDT"],
                "entry_rules": ["1h EMA50 rising", "15m pullback recovers EMA20", "RSI below 62"],
                "exit_rules": ["ATR stop", "Daily loss guard", "Time stop after 12 candles"],
                "risk_notes": "Designed to reduce trade frequency before the next backtest.",
                "created_at": now(),
            },
        ],
        "bot_templates": [
            {
                "id": "grid-guarded-spot",
                "name": "Guarded Spot Grid",
                "type": "grid",
                "exchange": "OKX",
                "pairs": ["BTC/USDT", "ETH/USDT"],
                "timeframe": "15m",
                "settings": {
                    "grid_levels": 8,
                    "range_source": "last_20_day_channel",
                    "per_grid_stake": 12.5,
                    "take_profit_per_grid_pct": 0.6,
                },
                "risk": ["spot only", "no leverage", "stop when price leaves channel", "dry-run approval required"],
                "status": "template",
            },
            {
                "id": "dca-trend-recovery",
                "name": "Trend Recovery DCA",
                "type": "dca",
                "exchange": "OKX",
                "pairs": ["BTC/USDT", "ETH/USDT"],
                "timeframe": "1h",
                "settings": {
                    "base_order": 25,
                    "safety_orders": 3,
                    "safety_order_step_pct": 2.5,
                    "max_total_stake": 100,
                },
                "risk": ["disable in downtrend", "max 3 safety orders", "daily loss guard", "dry-run approval required"],
                "status": "template",
            },
            {
                "id": "signal-trend-follow",
                "name": "Signal Trend Follow",
                "type": "signal",
                "exchange": "OKX",
                "pairs": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
                "timeframe": "15m + 1h",
                "settings": {
                    "source": "local rules",
                    "entry": "1h trend + 15m recovery",
                    "exit": "ema break or risk guard",
                },
                "risk": ["signals are advisory", "manual promotion only", "dry-run first"],
                "status": "template",
            },
        ],
        "alert_rules": [
            {"id": "drawdown-pause", "name": "总回撤暂停", "condition": "max_drawdown_pct >= 10", "severity": "high", "enabled": True},
            {"id": "loss-streak", "name": "连续亏损暂停", "condition": "max_consecutive_losses >= 3", "severity": "high", "enabled": True},
            {"id": "bot-stopped", "name": "主 Bot 未运行", "condition": "okx runtime != running", "severity": "medium", "enabled": True},
        ],
        "watchlist": [
            {"pair": "BTC/USDT", "exchange": "OKX", "role": "core", "enabled": True},
            {"pair": "ETH/USDT", "exchange": "OKX", "role": "core", "enabled": True},
            {"pair": "SOL/USDT", "exchange": "OKX", "role": "satellite", "enabled": True},
        ],
        "journal": [
            {
                "id": "initial-note",
                "created_at": now(),
                "title": "Stage 1 boundary",
                "body": "Run OKX spot dry-run first. Live trading stays locked until positive backtests and dry-run evidence exist.",
                "tags": ["safety", "dry-run"],
            }
        ],
        "tasks": [],
        "airdrop_workspace": _default_airdrop_workspace(),
    }


def _path() -> Path:
    return get_settings().state_path


def _merge_defaults(state: dict[str, Any]) -> dict[str, Any]:
    defaults = _default_state()
    changed = False
    for key, value in defaults.items():
        if key not in state:
            state[key] = value
            changed = True
    if "profile" in state:
        for key, value in defaults["profile"].items():
            if key not in state["profile"]:
                state["profile"][key] = value
                changed = True
    if "risk" in state:
        for key, value in defaults["risk"].items():
            if key not in state["risk"]:
                state["risk"][key] = value
                changed = True
    if "live_trading" in state:
        for key, value in defaults["live_trading"].items():
            if key not in state["live_trading"]:
                state["live_trading"][key] = value
                changed = True
    if "live_accounts" in state:
        for exchange, account in defaults["live_accounts"].items():
            if exchange not in state["live_accounts"]:
                state["live_accounts"][exchange] = account
                changed = True
            else:
                for key, value in account.items():
                    if key not in state["live_accounts"][exchange]:
                        state["live_accounts"][exchange][key] = value
                        changed = True
    if "airdrop_workspace" in state:
        airdrop_defaults = defaults["airdrop_workspace"]
        for key, value in airdrop_defaults.items():
            if key not in state["airdrop_workspace"]:
                state["airdrop_workspace"][key] = value
                changed = True
        settings = state["airdrop_workspace"].setdefault("settings", {})
        for key, value in airdrop_defaults["settings"].items():
            if key not in settings:
                settings[key] = value
                changed = True
        existing_projects = {item.get("id"): item for item in state["airdrop_workspace"].setdefault("projects", [])}
        for default_project in airdrop_defaults["projects"]:
            project_id = default_project["id"]
            if project_id not in existing_projects:
                state["airdrop_workspace"]["projects"].append(default_project)
                changed = True
                continue
            project = existing_projects[project_id]
            for key, value in default_project.items():
                if key not in project:
                    project[key] = value
                    changed = True
            existing_tasks = {item.get("id"): item for item in project.setdefault("tasks", [])}
            for default_task in default_project["tasks"]:
                if default_task["id"] not in existing_tasks:
                    project["tasks"].append(default_task)
                    changed = True
            source_fixes = {
                "grass-rewards": ("https://www.grassnetwork.xyz/", "https://app.getgrass.io/", "Official app"),
                "eclipse-season-watch": (
                    "https://www.eclipse.xyz/articles/introducing-es",
                    "https://www.eclipse.xyz/articles/everything-eclipse-ed-12",
                    "Everything Eclipse",
                ),
            }
            if project_id in source_fixes:
                old_url, new_url, label = source_fixes[project_id]
                if project.get("official_url") == old_url:
                    project["official_url"] = new_url
                    changed = True
                for source in project.get("sources", []):
                    if source.get("url") == old_url:
                        source["url"] = new_url
                        source["label"] = label
                        changed = True
    if changed:
        state["updated_at"] = now()
    return state


def read_state() -> dict[str, Any]:
    path = _path()
    with _LOCK:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            state = _default_state()
            path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            return deepcopy(state)
        state = _merge_defaults(json.loads(path.read_text(encoding="utf-8")))
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return deepcopy(state)


def write_state(state: dict[str, Any]) -> dict[str, Any]:
    state["updated_at"] = now()
    path = _path()
    with _LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    return deepcopy(state)


def append_task(action: str, bot_id: Optional[str] = None) -> dict[str, Any]:
    state = read_state()
    task = {
        "id": str(uuid4()),
        "action": action,
        "bot_id": bot_id,
        "status": "queued",
        "created_at": now(),
        "started_at": None,
        "finished_at": None,
        "returncode": None,
        "output_tail": "",
    }
    state.setdefault("tasks", []).insert(0, task)
    state["tasks"] = state["tasks"][:80]
    write_state(state)
    return task


def update_task(task_id: str, **updates: Any) -> Optional[dict[str, Any]]:
    state = read_state()
    for task in state.setdefault("tasks", []):
        if task["id"] == task_id:
            task.update(updates)
            write_state(state)
            return task
    return None


def create_strategy_draft(payload: dict[str, Any]) -> dict[str, Any]:
    state = read_state()
    draft = {
        "id": payload.get("id") or f"strategy-{uuid4().hex[:8]}",
        "name": payload["name"],
        "status": payload.get("status", "draft"),
        "timeframe": payload.get("timeframe", "15m"),
        "pairs": payload.get("pairs") or state["risk"]["allowed_pairs"],
        "entry_rules": payload.get("entry_rules", []),
        "exit_rules": payload.get("exit_rules", []),
        "risk_notes": payload.get("risk_notes", ""),
        "created_at": now(),
    }
    state.setdefault("strategy_drafts", []).insert(0, draft)
    write_state(state)
    return draft


def add_journal_entry(payload: dict[str, Any]) -> dict[str, Any]:
    state = read_state()
    entry = {
        "id": str(uuid4()),
        "created_at": now(),
        "title": payload["title"],
        "body": payload["body"],
        "tags": payload.get("tags", []),
    }
    state.setdefault("journal", []).insert(0, entry)
    write_state(state)
    return entry


def append_live_order(payload: dict[str, Any]) -> dict[str, Any]:
    state = read_state()
    order = {
        "id": str(uuid4()),
        "created_at": now(),
        **payload,
    }
    state.setdefault("live_orders", []).insert(0, order)
    state["live_orders"] = state["live_orders"][:200]
    write_state(state)
    return order


def update_live_order_status(exchange: str, order_id: str, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
    state = read_state()
    for order in state.setdefault("live_orders", []):
        identifiers = {
            str(order.get("id") or ""),
            str(order.get("external_order_id") or ""),
            str(order.get("client_order_id") or ""),
        }
        if order.get("exchange") == exchange and order_id in identifiers:
            order.update(updates)
            order["updated_at"] = now()
            write_state(state)
            return order
    return None
