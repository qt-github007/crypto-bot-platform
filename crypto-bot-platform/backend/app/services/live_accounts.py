from __future__ import annotations

import base64
import copy
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings
from app.services.freqtrade import freqtrade_dir
from app.services.state import append_live_order, now, read_state, update_live_order_status, write_state

SUPPORTED_EXCHANGES = {"okx", "binance"}
LIVE_CONFIGS = {
    "okx": "user_data/config_spot_live_okx.local.json",
    "binance": "user_data/config_spot_live_binance.local.json",
}
LIVE_EXAMPLES = {
    "okx": "user_data/config_spot_live_okx.example.json",
    "binance": "user_data/config_spot_live_binance.example.json",
}


def _validate_exchange(exchange: str) -> None:
    if exchange not in SUPPORTED_EXCHANGES:
        raise ValueError("Unsupported exchange.")


def _status_from_issues(issues: list[str]) -> str:
    return "blocked" if any("withdraw" in item.lower() for item in issues) else "connected"


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return f"{value[:2]}***{value[-2:]}"
    return f"{value[:4]}...{value[-4:]}"


def _env_key(exchange: str, name: str) -> str:
    return f"{exchange.upper()}_{name}"


def _read_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip().strip("'").strip('"')
    return result


def _write_env(values: dict[str, str]) -> Path:
    path = get_settings().live_env_path
    existing = _read_env(path)
    existing.update(values)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Local exchange secrets for live account connectivity.",
        "# Keep this file private. Never enable withdrawal permission on these keys.",
    ]
    for key in sorted(existing):
        escaped = existing[key].replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'{key}="{escaped}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)
    return path


def _okx_headers(api_key: str, secret: str, passphrase: str, method: str, request_path: str, body: str = "") -> dict[str, str]:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    payload = f"{timestamp}{method.upper()}{request_path}{body}"
    digest = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    signature = base64.b64encode(digest).decode("utf-8")
    return {
        "OK-ACCESS-KEY": api_key,
        "OK-ACCESS-SIGN": signature,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": passphrase,
        "Content-Type": "application/json",
    }


def _binance_signed_query(secret: str, params: dict[str, Any]) -> str:
    params = {**params, "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000), "recvWindow": 5000}
    query = urlencode(params)
    signature = hmac.new(secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{query}&signature={signature}"


def _top_balances(details: list[dict[str, Any]], currency_key: str, free_key: str, total_key: str) -> list[dict[str, Any]]:
    balances = []
    for item in details:
        free = float(item.get(free_key) or 0)
        total = float(item.get(total_key) or 0)
        if free or total:
            balances.append(
                {
                    "currency": item.get(currency_key),
                    "free": free,
                    "total": total,
                }
            )
    return sorted(balances, key=lambda row: row["total"], reverse=True)[:20]


def _connect_okx(api_key: str, api_secret: str, passphrase: str) -> dict[str, Any]:
    if not passphrase:
        raise ValueError("OKX requires an API passphrase.")
    base = "https://www.okx.com"
    with httpx.Client(timeout=12) as client:
        config_path = "/api/v5/account/config"
        config_response = client.get(base + config_path, headers=_okx_headers(api_key, api_secret, passphrase, "GET", config_path))
        config_response.raise_for_status()
        config = config_response.json()

        balance_path = "/api/v5/account/balance"
        balance_response = client.get(base + balance_path, headers=_okx_headers(api_key, api_secret, passphrase, "GET", balance_path))
        balance_response.raise_for_status()
        balance = balance_response.json()
    account = (config.get("data") or [{}])[0]
    balance_data = (balance.get("data") or [{}])[0]
    details = balance_data.get("details", [])
    perm_text = str(account.get("perm") or "").lower()
    permissions = {
        "raw": account.get("perm"),
        "can_read": "read" in perm_text or "read_only" in perm_text,
        "can_trade": "trade" in perm_text,
        "can_withdraw": "withdraw" in perm_text,
        "ip": account.get("ip") or "",
        "uid": account.get("uid") or "",
        "account_level": account.get("acctLv") or "",
    }
    return {
        "permissions": permissions,
        "balances": _top_balances(details, "ccy", "availBal", "eq"),
        "raw_status": {"config_code": config.get("code"), "balance_code": balance.get("code")},
    }


def _connect_binance(api_key: str, api_secret: str) -> dict[str, Any]:
    base = "https://api.binance.com"
    headers = {"X-MBX-APIKEY": api_key}
    with httpx.Client(timeout=12, headers=headers) as client:
        account_query = _binance_signed_query(api_secret, {})
        account_response = client.get(f"{base}/api/v3/account?{account_query}")
        account_response.raise_for_status()
        account = account_response.json()

        restriction_query = _binance_signed_query(api_secret, {})
        restriction_response = client.get(f"{base}/sapi/v1/account/apiRestrictions?{restriction_query}")
        restrictions = restriction_response.json() if restriction_response.status_code == 200 else {"error": restriction_response.text}
    permissions = {
        "can_read": True,
        "can_trade": bool(account.get("canTrade")),
        "can_withdraw": bool(account.get("canWithdraw") or restrictions.get("enableWithdrawals")),
        "can_deposit": bool(account.get("canDeposit")),
        "enable_spot_margin_trading": bool(restrictions.get("enableSpotAndMarginTrading")),
        "enable_futures": bool(restrictions.get("enableFutures")),
        "ip_restrict": bool(restrictions.get("ipRestrict")),
        "restriction_error": restrictions.get("error"),
    }
    return {
        "permissions": permissions,
        "balances": _top_balances(account.get("balances", []), "asset", "free", "free"),
        "raw_status": {"account_type": account.get("accountType"), "restriction_checked": "error" not in restrictions},
    }


def _permission_issues(exchange: str, permissions: dict[str, Any]) -> list[str]:
    issues = []
    if permissions.get("can_withdraw"):
        issues.append("API key has withdrawal permission. Disable withdrawals before using this console.")
    if not permissions.get("can_read"):
        issues.append("API key does not appear to have read permission.")
    if not permissions.get("can_trade"):
        issues.append("API key does not appear to have spot trading permission.")
    if exchange == "okx" and not permissions.get("ip"):
        issues.append("OKX API key is not IP-bound according to the account config response.")
    if exchange == "binance" and not permissions.get("ip_restrict"):
        issues.append("Binance API key does not appear to be IP-restricted.")
    if permissions.get("enable_futures"):
        issues.append("Futures permission is enabled; this console is spot-only.")
    return issues


def _base_live_config(exchange: str, credentials: Optional[dict[str, str]] = None) -> dict[str, Any]:
    dryrun_path = freqtrade_dir() / "user_data" / f"config_spot_dryrun_{exchange}.json"
    config = json.loads(dryrun_path.read_text(encoding="utf-8"))
    state = read_state()
    live = state["live_trading"]
    config["bot_name"] = f"freqtrade-agent-{exchange}-spot-live"
    config["initial_state"] = "stopped"
    config["dry_run"] = False
    config.pop("dry_run_wallet", None)
    config["stake_amount"] = min(float(live.get("max_live_stake_amount", 10)), 10)
    config["max_open_trades"] = min(int(live.get("max_live_open_trades", 1)), 1)
    config["tradable_balance_ratio"] = 0.25
    config["db_url"] = f"sqlite:////freqtrade/user_data/tradesv3_{exchange}_spot_live.sqlite"
    config["exchange"]["key"] = credentials.get("api_key", "") if credentials else ""
    config["exchange"]["secret"] = credentials.get("api_secret", "") if credentials else ""
    if exchange == "okx":
        config["exchange"]["password"] = credentials.get("passphrase", "") if credentials else ""
        config["exchange"]["enable_ws"] = False
    else:
        config["exchange"].pop("password", None)
    config["api_server"]["username"] = f"{exchange}-live"
    config["api_server"]["password"] = "CHANGE_ME_LOCAL_LIVE_ONLY"
    config["api_server"]["jwt_secret_key"] = "CHANGE_ME_LOCAL_LIVE_JWT"
    config["api_server"]["ws_token"] = "CHANGE_ME_LOCAL_LIVE_WS"
    return config


def write_live_config(exchange: str, credentials: Optional[dict[str, str]] = None, local: bool = False) -> Path:
    target = LIVE_CONFIGS[exchange] if local else LIVE_EXAMPLES[exchange]
    path = freqtrade_dir() / target
    config = _base_live_config(exchange, credentials=credentials if local else None)
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600 if local else 0o644)
    return path


def connect_exchange(payload: dict[str, Any]) -> dict[str, Any]:
    exchange = payload["exchange"]
    _validate_exchange(exchange)
    credentials = {
        "api_key": payload["api_key"],
        "api_secret": payload["api_secret"],
        "passphrase": payload.get("passphrase", ""),
    }
    result: dict[str, Any] = {
        "exchange": exchange,
        "status": "not_tested",
        "permissions": {},
        "balances": [],
        "raw_status": {},
        "issues": [],
    }
    if payload.get("test_connection", True):
        if exchange == "okx":
            result.update(_connect_okx(credentials["api_key"], credentials["api_secret"], credentials["passphrase"]))
        else:
            result.update(_connect_binance(credentials["api_key"], credentials["api_secret"]))
        result["issues"] = _permission_issues(exchange, result["permissions"])
        result["status"] = _status_from_issues(result["issues"])
    else:
        result["status"] = "saved_without_network_test"
        result["issues"] = ["Connection was not tested against the exchange."]
    env_path = None
    local_config_path = None
    if payload.get("save_to_env"):
        values = {
            _env_key(exchange, "API_KEY"): credentials["api_key"],
            _env_key(exchange, "API_SECRET"): credentials["api_secret"],
        }
        if exchange == "okx":
            values[_env_key(exchange, "API_PASSPHRASE")] = credentials["passphrase"]
        env_path = _write_env(values)
    if payload.get("generate_live_config", True):
        write_live_config(exchange, local=False)
        if payload.get("save_to_env"):
            local_config_path = write_live_config(exchange, credentials=credentials, local=True)
    state = read_state()
    account = state["live_accounts"][exchange]
    account.update(
        {
            "label": payload.get("label") or exchange.upper(),
            "status": result["status"],
            "masked_api_key": mask_secret(credentials["api_key"]),
            "permissions": result.get("permissions", {}),
            "balances": result.get("balances", []),
            "last_checked_at": now(),
            "saved_to_env": bool(payload.get("save_to_env")),
            "env_path": str(env_path) if env_path else account.get("env_path", ""),
            "config_path": str(local_config_path) if local_config_path else str(freqtrade_dir() / LIVE_EXAMPLES[exchange]),
            "issues": result.get("issues", []),
        }
    )
    write_state(state)
    return {**result, "masked_api_key": account["masked_api_key"], "saved_to_env": account["saved_to_env"], "config_path": account["config_path"]}


def refresh_live_account(exchange: str) -> dict[str, Any]:
    _validate_exchange(exchange)
    credentials = _credentials_from_env(exchange)
    if exchange == "okx":
        result = _connect_okx(credentials["api_key"], credentials["api_secret"], credentials["passphrase"])
    else:
        result = _connect_binance(credentials["api_key"], credentials["api_secret"])
    result["issues"] = _permission_issues(exchange, result["permissions"])
    result["status"] = _status_from_issues(result["issues"])

    state = read_state()
    account = state["live_accounts"][exchange]
    local_config = freqtrade_dir() / LIVE_CONFIGS[exchange]
    fallback_config = freqtrade_dir() / LIVE_EXAMPLES[exchange]
    account.update(
        {
            "status": result["status"],
            "masked_api_key": mask_secret(credentials["api_key"]),
            "permissions": result.get("permissions", {}),
            "balances": result.get("balances", []),
            "last_checked_at": now(),
            "saved_to_env": True,
            "env_path": str(get_settings().live_env_path),
            "config_path": account.get("config_path") or str(local_config if local_config.exists() else fallback_config),
            "issues": result.get("issues", []),
        }
    )
    write_state(state)
    return {**result, "masked_api_key": account["masked_api_key"], "saved_to_env": True, "config_path": account["config_path"]}


def live_status() -> dict[str, Any]:
    state = read_state()
    accounts = copy.deepcopy(state["live_accounts"])
    for exchange, account in accounts.items():
        account["example_config_exists"] = (freqtrade_dir() / LIVE_EXAMPLES[exchange]).exists()
        account["local_config_exists"] = (freqtrade_dir() / LIVE_CONFIGS[exchange]).exists()
    return {
        "live_trading": state["live_trading"],
        "accounts": accounts,
        "env_path": str(get_settings().live_env_path),
        "env_exists": get_settings().live_env_path.exists(),
        "preflight": live_preflight(),
    }


def live_preflight(exchange: Optional[str] = None) -> dict[str, Any]:
    state = read_state()
    exchanges = [exchange] if exchange else list(SUPPORTED_EXCHANGES)
    checks = []
    for name in exchanges:
        account = state["live_accounts"][name]
        permissions = account.get("permissions", {})
        local_config = freqtrade_dir() / LIVE_CONFIGS[name]
        checks.extend(
            [
                {"exchange": name, "code": "account_connected", "passed": account.get("status") == "connected", "message": "Exchange account must be tested and connected."},
                {"exchange": name, "code": "no_withdraw", "passed": not permissions.get("can_withdraw"), "message": "Withdrawal permission must be disabled."},
                {"exchange": name, "code": "can_trade", "passed": bool(permissions.get("can_trade")), "message": "Spot trading permission should be enabled."},
                {"exchange": name, "code": "local_config", "passed": local_config.exists(), "message": "Local live config file must exist."},
                {"exchange": name, "code": "env_file", "passed": get_settings().live_env_path.exists(), "message": "Local live env file must exist."},
            ]
        )
    return {"passed": all(item["passed"] for item in checks), "checks": checks}


def assert_live_start_allowed(exchange: str, ack: str) -> dict[str, Any]:
    state = read_state()
    required_ack = state["live_trading"]["ack_required"]
    if ack != required_ack:
        raise ValueError(f"Live start requires exact acknowledgement: {required_ack}")
    preflight = live_preflight(exchange)
    if not preflight["passed"]:
        raise ValueError("Live preflight failed. Fix connection, permissions and local config first.")
    return preflight


def _credentials_from_env(exchange: str) -> dict[str, str]:
    values = _read_env(get_settings().live_env_path)
    credentials = {
        "api_key": values.get(_env_key(exchange, "API_KEY"), ""),
        "api_secret": values.get(_env_key(exchange, "API_SECRET"), ""),
        "passphrase": values.get(_env_key(exchange, "API_PASSPHRASE"), ""),
    }
    if not credentials["api_key"] or not credentials["api_secret"]:
        raise ValueError(f"{exchange.upper()} credentials are missing from {get_settings().live_env_path}.")
    if exchange == "okx" and not credentials["passphrase"]:
        raise ValueError("OKX passphrase is missing from the live env file.")
    return credentials


def _assert_allowed_pair(pair: str) -> None:
    allowed_pairs = read_state()["risk"].get("allowed_pairs", [])
    if pair not in allowed_pairs:
        raise ValueError(f"{pair} is not in allowed_pairs.")


def _assert_exchange_api_ready(exchange: str, require_trade: bool = False) -> dict[str, Any]:
    _validate_exchange(exchange)
    account = read_state()["live_accounts"][exchange]
    if account.get("status") != "connected":
        raise ValueError(f"{exchange.upper()} account must be connected and refreshed before this action.")
    permissions = account.get("permissions", {})
    if permissions.get("can_withdraw"):
        raise ValueError("Withdrawal permission is enabled. Disable withdrawals before using live account actions.")
    if not permissions.get("can_read"):
        raise ValueError("Read permission is required for live account actions.")
    if require_trade and not permissions.get("can_trade"):
        raise ValueError("Spot trading permission is required for this live account action.")
    return account


def _timestamp_ms_to_iso(value: Any) -> str:
    try:
        timestamp = int(value)
    except (TypeError, ValueError):
        return ""
    if timestamp <= 0:
        return ""
    return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).isoformat(timespec="seconds")


def _pair_to_okx(pair: str) -> str:
    return pair.replace("/", "-")


def _pair_to_binance(pair: str) -> str:
    return pair.replace("/", "")


def _symbol_to_pair(symbol: str) -> str:
    for quote in ("USDT", "USDC", "BTC", "ETH"):
        if symbol.endswith(quote) and len(symbol) > len(quote):
            return f"{symbol[:-len(quote)]}/{quote}"
    return symbol


def _format_amount(value: float) -> str:
    return f"{value:.8f}".rstrip("0").rstrip(".")


def _ensure_okx_success(payload: dict[str, Any]) -> None:
    if str(payload.get("code", "0")) != "0":
        raise ValueError(f"OKX API error {payload.get('code')}: {payload.get('msg') or payload}")


def _okx_signed_get(credentials: dict[str, str], path: str, params: dict[str, Any]) -> dict[str, Any]:
    clean_params = {key: value for key, value in params.items() if value not in (None, "")}
    query = urlencode(clean_params)
    request_path = f"{path}?{query}" if query else path
    response = httpx.get(
        "https://www.okx.com" + request_path,
        headers=_okx_headers(credentials["api_key"], credentials["api_secret"], credentials["passphrase"], "GET", request_path),
        timeout=12,
    )
    response.raise_for_status()
    payload = response.json()
    _ensure_okx_success(payload)
    return payload


def _okx_signed_post(credentials: dict[str, str], path: str, body: dict[str, Any]) -> dict[str, Any]:
    clean_body = {key: value for key, value in body.items() if value not in (None, "")}
    body_text = json.dumps(clean_body, separators=(",", ":"))
    response = httpx.post(
        "https://www.okx.com" + path,
        headers=_okx_headers(credentials["api_key"], credentials["api_secret"], credentials["passphrase"], "POST", path, body_text),
        content=body_text,
        timeout=12,
    )
    response.raise_for_status()
    payload = response.json()
    _ensure_okx_success(payload)
    return payload


def _binance_signed_request(method: str, endpoint: str, credentials: dict[str, str], params: dict[str, Any]) -> dict[str, Any]:
    clean_params = {key: value for key, value in params.items() if value not in (None, "")}
    query = _binance_signed_query(credentials["api_secret"], clean_params)
    response = httpx.request(
        method,
        f"https://api.binance.com{endpoint}?{query}",
        headers={"X-MBX-APIKEY": credentials["api_key"]},
        timeout=12,
    )
    response.raise_for_status()
    return response.json()


def _normalize_okx_order(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "exchange": "okx",
        "pair": str(item.get("instId") or "").replace("-", "/"),
        "order_id": item.get("ordId") or "",
        "client_order_id": item.get("clOrdId") or "",
        "side": item.get("side") or "",
        "order_type": item.get("ordType") or "",
        "price": item.get("px") or "",
        "amount": item.get("sz") or "",
        "filled": item.get("accFillSz") or "",
        "quote_filled": item.get("fillNotionalUsd") or item.get("fillPx") or "",
        "status": item.get("state") or "",
        "created_at": _timestamp_ms_to_iso(item.get("cTime")),
        "updated_at": _timestamp_ms_to_iso(item.get("uTime")),
        "raw": item,
    }


def _normalize_binance_order(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "exchange": "binance",
        "pair": _symbol_to_pair(str(item.get("symbol") or "")),
        "order_id": str(item.get("orderId") or ""),
        "client_order_id": item.get("clientOrderId") or "",
        "side": str(item.get("side") or "").lower(),
        "order_type": str(item.get("type") or "").lower(),
        "price": item.get("price") or "",
        "amount": item.get("origQty") or "",
        "filled": item.get("executedQty") or "",
        "quote_filled": item.get("cummulativeQuoteQty") or "",
        "status": str(item.get("status") or "").lower(),
        "created_at": _timestamp_ms_to_iso(item.get("time")),
        "updated_at": _timestamp_ms_to_iso(item.get("updateTime")),
        "raw": item,
    }


def preview_live_order(payload: dict[str, Any]) -> dict[str, Any]:
    state = read_state()
    risk = state["risk"]
    exchange = payload["exchange"]
    pair = payload["pair"]
    order_type = payload.get("order_type", "limit")
    side = payload["side"]
    quote_amount = float(payload["quote_amount"])
    price = payload.get("price")
    issues = []
    if pair not in risk.get("allowed_pairs", []):
        issues.append(f"{pair} is not in allowed_pairs.")
    if quote_amount > float(state["live_trading"].get("max_live_stake_amount", 10)):
        issues.append("Order quote amount exceeds max_live_stake_amount.")
    if order_type == "limit" and not price:
        issues.append("Limit order requires a price.")
    if order_type == "market" and side == "sell":
        issues.append("Market sell is disabled in this console to avoid base-amount ambiguity.")
    base_amount = quote_amount / float(price) if price else None
    return {
        "exchange": exchange,
        "pair": pair,
        "side": side,
        "order_type": order_type,
        "quote_amount": quote_amount,
        "price": price,
        "base_amount_estimate": base_amount,
        "max_allowed_quote_amount": state["live_trading"].get("max_live_stake_amount", 10),
        "requires_ack": state["live_trading"]["ack_required"],
        "issues": issues,
        "passed": not issues,
    }


def _assert_live_order_allowed(payload: dict[str, Any]) -> dict[str, Any]:
    state = read_state()
    required_ack = state["live_trading"]["ack_required"]
    if payload.get("ack") != required_ack:
        raise ValueError(f"Live order requires exact acknowledgement: {required_ack}")
    preview = preview_live_order(payload)
    if not preview["passed"]:
        raise ValueError("; ".join(preview["issues"]))
    preflight = live_preflight(payload["exchange"])
    if not preflight["passed"]:
        raise ValueError("Live order preflight failed. Connect account, disable withdrawals and save local config first.")
    return preview


def _place_okx_order(payload: dict[str, Any], credentials: dict[str, str], preview: dict[str, Any]) -> dict[str, Any]:
    body = {
        "instId": _pair_to_okx(payload["pair"]),
        "tdMode": "cash",
        "side": payload["side"],
        "ordType": payload["order_type"],
    }
    if payload["order_type"] == "limit":
        body["px"] = _format_amount(float(payload["price"]))
        body["sz"] = _format_amount(float(preview["base_amount_estimate"]))
    else:
        body["tgtCcy"] = "quote_ccy"
        body["sz"] = _format_amount(float(payload["quote_amount"]))
    return _okx_signed_post(credentials, "/api/v5/trade/order", body)


def _place_binance_order(payload: dict[str, Any], credentials: dict[str, str], preview: dict[str, Any]) -> dict[str, Any]:
    params: dict[str, Any] = {
        "symbol": _pair_to_binance(payload["pair"]),
        "side": payload["side"].upper(),
        "type": payload["order_type"].upper(),
        "newOrderRespType": "FULL",
    }
    if payload["order_type"] == "limit":
        params["timeInForce"] = "GTC"
        params["price"] = _format_amount(float(payload["price"]))
        params["quantity"] = _format_amount(float(preview["base_amount_estimate"]))
    else:
        params["quoteOrderQty"] = _format_amount(float(payload["quote_amount"]))
    query = _binance_signed_query(credentials["api_secret"], params)
    response = httpx.post("https://api.binance.com/api/v3/order?" + query, headers={"X-MBX-APIKEY": credentials["api_key"]}, timeout=12)
    response.raise_for_status()
    return response.json()


def _submitted_order_ids(exchange: str, response: dict[str, Any]) -> dict[str, str]:
    if exchange == "okx":
        data = response.get("data") or [{}]
        item = data[0] if data else {}
        return {"external_order_id": str(item.get("ordId") or ""), "client_order_id": str(item.get("clOrdId") or "")}
    return {"external_order_id": str(response.get("orderId") or ""), "client_order_id": str(response.get("clientOrderId") or "")}


def place_live_order(payload: dict[str, Any]) -> dict[str, Any]:
    preview = _assert_live_order_allowed(payload)
    exchange = payload["exchange"]
    credentials = _credentials_from_env(exchange)
    if exchange == "okx":
        response = _place_okx_order(payload, credentials, preview)
    else:
        response = _place_binance_order(payload, credentials, preview)
    order = append_live_order(
        {
            "exchange": exchange,
            "pair": payload["pair"],
            "side": payload["side"],
            "order_type": payload["order_type"],
            "quote_amount": payload["quote_amount"],
            "price": payload.get("price"),
            "status": "submitted",
            **_submitted_order_ids(exchange, response),
            "response": response,
            "preview": preview,
        }
    )
    return {"order": order, "exchange_response": response}


def fetch_exchange_orders(exchange: str, view: str, pair: Optional[str] = None) -> dict[str, Any]:
    _validate_exchange(exchange)
    if view not in {"open", "history"}:
        raise ValueError("Unsupported order view.")
    if pair:
        _assert_allowed_pair(pair)
    if exchange == "binance" and not pair:
        raise ValueError("Binance order queries require a pair filter.")
    _assert_exchange_api_ready(exchange, require_trade=False)
    credentials = _credentials_from_env(exchange)

    if exchange == "okx":
        path = "/api/v5/trade/orders-pending" if view == "open" else "/api/v5/trade/orders-history"
        params = {"instType": "SPOT", "instId": _pair_to_okx(pair) if pair else "", "limit": "50"}
        payload = _okx_signed_get(credentials, path, params)
        orders = [_normalize_okx_order(item) for item in payload.get("data", [])]
        return {"exchange": exchange, "view": view, "pair": pair, "orders": orders, "raw_status": {"code": payload.get("code")}}

    endpoint = "/api/v3/openOrders" if view == "open" else "/api/v3/allOrders"
    params = {"symbol": _pair_to_binance(pair or "")}
    if view == "history":
        params["limit"] = 50
    payload = _binance_signed_request("GET", endpoint, credentials, params)
    orders = [_normalize_binance_order(item) for item in payload]
    return {"exchange": exchange, "view": view, "pair": pair, "orders": orders, "raw_status": {"count": len(orders)}}


def cancel_live_order(payload: dict[str, Any]) -> dict[str, Any]:
    exchange = payload["exchange"]
    pair = payload["pair"]
    order_id = payload.get("order_id") or ""
    client_order_id = payload.get("client_order_id") or ""
    required_ack = read_state()["live_trading"]["ack_required"]
    if payload.get("ack") != required_ack:
        raise ValueError(f"Live cancel requires exact acknowledgement: {required_ack}")
    if not order_id and not client_order_id:
        raise ValueError("Cancel requires order_id or client_order_id.")
    _assert_allowed_pair(pair)
    _assert_exchange_api_ready(exchange, require_trade=True)
    credentials = _credentials_from_env(exchange)

    if exchange == "okx":
        response = _okx_signed_post(
            credentials,
            "/api/v5/trade/cancel-order",
            {"instId": _pair_to_okx(pair), "ordId": order_id, "clOrdId": client_order_id},
        )
    else:
        params = {"symbol": _pair_to_binance(pair)}
        if order_id:
            params["orderId"] = order_id
        if client_order_id:
            params["origClientOrderId"] = client_order_id
        response = _binance_signed_request("DELETE", "/api/v3/order", credentials, params)

    lookup_id = order_id or client_order_id
    local_order = update_live_order_status(
        exchange,
        lookup_id,
        {"status": "canceled", "cancel_response": response},
    )
    return {"exchange": exchange, "pair": pair, "order_id": order_id, "client_order_id": client_order_id, "status": "cancel_requested", "local_order": local_order, "exchange_response": response}


def list_live_orders() -> list[dict[str, Any]]:
    return read_state().get("live_orders", [])
