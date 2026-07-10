from __future__ import annotations

import json
import sqlite3
import subprocess
import threading
from pathlib import Path
from typing import Any, Optional
from zipfile import ZipFile

import httpx

from app.core.config import get_settings
from app.services.state import append_task, now, update_task


BOT_DEFS = {
    "okx_spot_dryrun": {
        "id": "okx_spot_dryrun",
        "name": "OKX Spot Dry-run",
        "exchange": "okx",
        "container": "freqtrade-agent-okx-dryrun",
        "config": "user_data/config_spot_dryrun_okx.json",
        "port": 8081,
        "primary": True,
        "recommended": True,
        "actions": ["setup", "download-okx", "backtest-okx", "dryrun-okx", "stop"],
    },
    "binance_spot_dryrun": {
        "id": "binance_spot_dryrun",
        "name": "Binance Spot Dry-run",
        "exchange": "binance",
        "container": "freqtrade-agent-binance-dryrun",
        "config": "user_data/config_spot_dryrun_binance.json",
        "port": 8080,
        "primary": False,
        "recommended": False,
        "actions": ["setup", "download-binance", "backtest-binance", "dryrun-binance", "stop"],
        "warning": "Current network has previously hit Binance 418/-1003 limitations.",
    },
}

ALLOWED_ACTIONS = {
    "setup",
    "download-okx",
    "download-binance",
    "backtest-okx",
    "backtest-binance",
    "dryrun-okx",
    "dryrun-binance",
    "stop",
}

LIVE_ACTIONS = {
    "live-okx",
    "live-binance",
}

FORBIDDEN_ACTIONS = {"live", "trade-live", "withdraw", "futures", "margin", "short", "leverage"}


def freqtrade_dir() -> Path:
    return get_settings().freqtrade_dir


def _read_config(bot: dict[str, Any]) -> dict[str, Any]:
    path = freqtrade_dir() / bot["config"]
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _run(args: list[str], timeout: int = 8) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=freqtrade_dir(),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def docker_status(bot: dict[str, Any]) -> dict[str, Any]:
    try:
        result = _run(["docker", "inspect", "-f", "{{.State.Status}}|{{.State.StartedAt}}", bot["container"]], timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"state": "unavailable", "detail": str(exc)}
    if result.returncode != 0:
        return {"state": "stopped", "detail": result.stderr.strip() or "container not found"}
    state, _, started = result.stdout.strip().partition("|")
    return {"state": state or "unknown", "started_at": started or None}


def api_ping(bot: dict[str, Any]) -> dict[str, Any]:
    url = f"http://127.0.0.1:{bot['port']}/api/v1/ping"
    try:
        response = httpx.get(url, timeout=2)
        if response.status_code == 200:
            return {"reachable": True, "url": url, "response": response.json()}
        return {"reachable": False, "url": url, "status_code": response.status_code}
    except Exception as exc:
        return {"reachable": False, "url": url, "error": str(exc)}


def safety_audit(bot_id: str) -> dict[str, Any]:
    bot = BOT_DEFS[bot_id]
    config = _read_config(bot)
    strategy_path = freqtrade_dir() / "user_data" / "strategies" / "HybridSafeStrategy.py"
    strategy_text = strategy_path.read_text(encoding="utf-8") if strategy_path.exists() else ""
    exchange = config.get("exchange", {})
    api_server = config.get("api_server", {})
    checks = [
        ("dry_run", config.get("dry_run") is True, "Config must keep dry_run true."),
        ("spot_only", config.get("trading_mode") == "spot", "Trading mode must be spot."),
        ("no_margin", not config.get("margin_mode"), "Margin mode must stay empty."),
        ("no_short", "can_short = False" in strategy_text, "Strategy must not allow shorting."),
        ("no_keys_in_json", not any(exchange.get(k) for k in ["key", "secret", "password"]), "API keys must not be stored in JSON."),
        ("local_webui", api_server.get("listen_ip_address") == "127.0.0.1", "API server must bind to localhost."),
        ("stake_limit", float(config.get("stake_amount", 999999)) <= 50, "Stake amount must be <= 50 USDT."),
        ("trade_limit", int(config.get("max_open_trades", 999999)) <= 3, "Max open trades must be <= 3."),
    ]
    return {
        "bot_id": bot_id,
        "passed": all(item[1] for item in checks),
        "checks": [{"code": code, "passed": passed, "message": message} for code, passed, message in checks],
    }


def trade_db_summary(exchange: str) -> dict[str, Any]:
    db_path = freqtrade_dir() / "user_data" / f"tradesv3_{exchange}_spot_dryrun.sqlite"
    if not db_path.exists():
        return {"exists": False, "open_trades": 0, "closed_trades": 0, "realized_profit": 0.0, "latest_trades": []}
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        summary = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN is_open THEN 1 ELSE 0 END) AS open_trades,
                SUM(CASE WHEN NOT is_open THEN 1 ELSE 0 END) AS closed_trades,
                COALESCE(SUM(COALESCE(close_profit_abs, 0)), 0) AS realized_profit
            FROM trades
            """
        ).fetchone()
        rows = conn.execute(
            """
            SELECT pair, is_open, stake_amount, amount, open_rate, close_rate, close_profit_abs, open_date, close_date, exit_reason
            FROM trades
            ORDER BY id DESC
            LIMIT 12
            """
        ).fetchall()
        open_rows = conn.execute(
            """
            SELECT pair, stake_amount, amount, open_rate, open_date, strategy, enter_tag, stop_loss
            FROM trades
            WHERE is_open
            ORDER BY id DESC
            LIMIT 30
            """
        ).fetchall()
    except sqlite3.Error as exc:
        return {"exists": True, "error": str(exc), "open_trades": 0, "closed_trades": 0, "realized_profit": 0.0, "latest_trades": []}
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return {
        "exists": True,
        "total": int(summary["total"] or 0),
        "open_trades": int(summary["open_trades"] or 0),
        "closed_trades": int(summary["closed_trades"] or 0),
        "realized_profit": round(float(summary["realized_profit"] or 0), 4),
        "latest_trades": [dict(row) for row in rows],
        "open_positions": [dict(row) for row in open_rows],
    }


def bot_card(bot_id: str) -> dict[str, Any]:
    bot = BOT_DEFS[bot_id]
    config = _read_config(bot)
    status = docker_status(bot)
    return {
        **bot,
        "config_summary": {
            "strategy": config.get("strategy"),
            "timeframe": config.get("timeframe"),
            "stake_amount": config.get("stake_amount"),
            "max_open_trades": config.get("max_open_trades"),
            "dry_run_wallet": config.get("dry_run_wallet"),
            "pairs": config.get("exchange", {}).get("pair_whitelist", []),
            "dry_run": config.get("dry_run"),
            "trading_mode": config.get("trading_mode"),
        },
        "runtime": status,
        "api": api_ping(bot) if status.get("state") == "running" else {"reachable": False, "url": f"http://127.0.0.1:{bot['port']}"},
        "safety": safety_audit(bot_id),
        "trades": trade_db_summary(bot["exchange"]),
    }


def list_bots() -> list[dict[str, Any]]:
    return [bot_card(bot_id) for bot_id in BOT_DEFS]


def tail_logs(bot_id: str, lines: int = 200) -> dict[str, Any]:
    bot = BOT_DEFS[bot_id]
    try:
        result = _run(["docker", "logs", "--tail", str(lines), bot["container"]], timeout=8)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"bot_id": bot_id, "output": "", "error": str(exc)}
    return {
        "bot_id": bot_id,
        "output": (result.stdout + result.stderr)[-20000:],
        "returncode": result.returncode,
    }


def _read_zip_metrics(path: Path) -> Optional[dict[str, Any]]:
    try:
        with ZipFile(path) as archive:
            json_names = [name for name in archive.namelist() if name.endswith(".json") and "_config" not in name]
            if not json_names:
                return None
            payload = json.loads(archive.read(json_names[0]))
    except Exception:
        return None
    strategies = payload.get("strategy", {})
    if not strategies:
        return None
    strategy_name, result = next(iter(strategies.items()))
    note = ""
    meta_path = path.with_suffix(".meta.json")
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            note = next(iter(meta.values())).get("notes", "")
        except Exception:
            note = ""
    exchange = "okx" if "okx" in note.lower() else "binance" if "binance" in note.lower() else "unknown"
    return {
        "id": path.stem,
        "file": str(path),
        "exchange": exchange,
        "strategy": strategy_name,
        "timeframe": result.get("timeframe"),
        "start": result.get("backtest_start"),
        "end": result.get("backtest_end"),
        "total_trades": result.get("total_trades", 0),
        "profit_abs": round(float(result.get("profit_total_abs") or 0), 4),
        "profit_pct": round(float(result.get("profit_total") or 0) * 100, 2),
        "winrate_pct": round(float(result.get("winrate") or 0) * 100, 2),
        "max_drawdown_pct": round(float(result.get("max_drawdown_account") or 0) * 100, 2),
        "max_drawdown_abs": round(float(result.get("max_drawdown_abs") or 0), 4),
        "max_consecutive_losses": result.get("max_consecutive_losses", 0),
        "profit_factor": result.get("profit_factor"),
        "notes": note,
    }


def list_backtests() -> list[dict[str, Any]]:
    directory = freqtrade_dir() / "user_data" / "backtest_results"
    if not directory.exists():
        return []
    results = []
    for path in sorted(directory.glob("*.zip"), key=lambda item: item.stat().st_mtime, reverse=True):
        metrics = _read_zip_metrics(path)
        if metrics:
            results.append(metrics)
    return results


def portfolio_snapshot() -> dict[str, Any]:
    bots = [bot_card(bot_id) for bot_id in BOT_DEFS]
    positions = []
    realized_profit = 0.0
    open_exposure = 0.0
    for bot in bots:
        trades = bot.get("trades", {})
        realized_profit += float(trades.get("realized_profit") or 0)
        for item in trades.get("open_positions", []):
            stake = float(item.get("stake_amount") or 0)
            open_exposure += stake
            positions.append(
                {
                    **item,
                    "bot_id": bot["id"],
                    "exchange": bot["exchange"],
                    "market_value_estimate": stake,
                }
            )
    wallet = 1000.0
    return {
        "paper_wallet": wallet,
        "realized_profit": round(realized_profit, 4),
        "open_exposure": round(open_exposure, 4),
        "available_estimate": round(wallet + realized_profit - open_exposure, 4),
        "positions": positions,
        "bots": bots,
    }


def derived_signals() -> list[dict[str, Any]]:
    backtests = list_backtests()
    okx = next((item for item in backtests if item["exchange"] == "okx"), None)
    signals = [
        {
            "id": "risk-stop-loss-streak",
            "pair": "ALL",
            "source": "backtest risk",
            "direction": "pause",
            "confidence": 0.92,
            "message": "历史回测最大连续亏损高于阈值，策略进入观察/降频阶段。",
            "evidence": f"max_consecutive_losses={okx.get('max_consecutive_losses')}" if okx else "no okx backtest",
            "action": "Do not promote to live. Tune filters and rerun backtest.",
        },
        {
            "id": "trend-filter-upgrade",
            "pair": "BTC/USDT,ETH/USDT",
            "source": "strategy lab",
            "direction": "research",
            "confidence": 0.76,
            "message": "建议加入 1h 趋势过滤和交易频率限制，优先降低亏损串。",
            "evidence": "HybridSafeStrategy trades too frequently in prior backtests.",
            "action": "Create a new draft from Trend Filter template.",
        },
        {
            "id": "okx-primary-route",
            "pair": "OKX",
            "source": "runtime",
            "direction": "prefer",
            "confidence": 0.84,
            "message": "当前本机环境优先使用 OKX dry-run，Binance 作为备用观察。",
            "evidence": "Binance previously hit upstream restrictions; OKX config disables websocket.",
            "action": "Use OKX for first paper trading run.",
        },
    ]
    return signals


def derived_alerts(risk: dict[str, Any]) -> list[dict[str, Any]]:
    alerts = []
    backtests = list_backtests()
    okx = next((item for item in backtests if item["exchange"] == "okx"), None)
    okx_bot = bot_card("okx_spot_dryrun")
    if okx and okx["max_drawdown_pct"] >= float(risk.get("pause_drawdown_pct", 10)):
        alerts.append(
            {
                "id": "okx-drawdown-pause",
                "severity": "high",
                "title": "OKX 回测回撤触发暂停观察",
                "detail": f"max_drawdown_pct={okx['max_drawdown_pct']} >= {risk.get('pause_drawdown_pct')}%",
            }
        )
    if okx and okx["max_consecutive_losses"] >= int(risk.get("max_consecutive_losses", 3)):
        alerts.append(
            {
                "id": "okx-loss-streak",
                "severity": "high",
                "title": "OKX 连续亏损超过阈值",
                "detail": f"max_consecutive_losses={okx['max_consecutive_losses']} >= {risk.get('max_consecutive_losses')}",
            }
        )
    if okx_bot.get("runtime", {}).get("state") != "running":
        alerts.append(
            {
                "id": "okx-not-running",
                "severity": "medium",
                "title": "OKX dry-run 当前未运行",
                "detail": f"runtime={okx_bot.get('runtime', {}).get('state')}",
            }
        )
    return alerts


def run_allowed_action(task_id: str, action: str) -> None:
    update_task(task_id, status="running", started_at=now())
    timeout = get_settings().command_timeout_seconds
    try:
        result = _run(["make", action], timeout=timeout)
        output = (result.stdout + result.stderr)[-30000:]
        update_task(
            task_id,
            status="success" if result.returncode == 0 else "failed",
            finished_at=now(),
            returncode=result.returncode,
            output_tail=output,
        )
    except subprocess.TimeoutExpired as exc:
        update_task(task_id, status="failed", finished_at=now(), returncode=124, output_tail=str(exc))
    except Exception as exc:
        update_task(task_id, status="failed", finished_at=now(), returncode=1, output_tail=str(exc))


def schedule_action(action: str, bot_id: Optional[str] = None) -> dict[str, Any]:
    action_lower = action.strip().lower()
    if action_lower in FORBIDDEN_ACTIONS or any(token in action_lower for token in FORBIDDEN_ACTIONS):
        raise ValueError("Live, withdrawal, futures, margin, shorting and leverage actions are locked.")
    if action_lower not in ALLOWED_ACTIONS:
        raise ValueError(f"Unsupported action: {action}")
    if bot_id and bot_id in BOT_DEFS and action_lower not in BOT_DEFS[bot_id]["actions"]:
        raise ValueError(f"Action {action} is not available for bot {bot_id}.")
    task = append_task(action_lower, bot_id=bot_id)
    worker = threading.Thread(target=run_allowed_action, args=(task["id"], action_lower), daemon=True)
    worker.start()
    return task


def schedule_live_action(exchange: str) -> dict[str, Any]:
    action = f"live-{exchange}"
    if action not in LIVE_ACTIONS:
        raise ValueError(f"Unsupported live action: {action}")
    task = append_task(action, bot_id=f"{exchange}_spot_live")
    worker = threading.Thread(target=run_allowed_action, args=(task["id"], action), daemon=True)
    worker.start()
    return task
