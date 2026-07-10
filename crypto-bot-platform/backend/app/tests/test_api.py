from __future__ import annotations

import os
import tempfile

tmpdir = tempfile.TemporaryDirectory()
os.environ["CRYPTO_CONSOLE_STATE_PATH"] = f"{tmpdir.name}/state.json"
os.environ["CRYPTO_CONSOLE_LIVE_ENV_PATH"] = f"{tmpdir.name}/.env.live.local"

from fastapi.testclient import TestClient

from app.core.config import get_settings

get_settings.cache_clear()

from app.main import app


client = TestClient(app)


def test_health_and_overview() -> None:
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["mode"] == "single_user_live_connection_ready"

    overview = client.get("/api/overview")
    assert overview.status_code == 200
    payload = overview.json()
    assert payload["safety"]["live_trading"] == "preflight_required"
    assert payload["primary_bot"]["id"] == "okx_spot_dryrun"


def test_live_actions_are_rejected() -> None:
    response = client.post("/api/actions", json={"action": "live"})
    assert response.status_code == 400
    assert "locked" in response.text.lower()


def test_strategy_draft_creation() -> None:
    response = client.post(
        "/api/strategies",
        json={
            "name": "Unit Test Draft",
            "timeframe": "15m",
            "pairs": ["BTC/USDT"],
            "entry_rules": ["RSI below 45", "EMA20 above EMA50"],
            "exit_rules": ["RSI above 70"],
            "risk_notes": "Test only",
        },
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Unit Test Draft"


def test_product_modules() -> None:
    portfolio = client.get("/api/portfolio")
    assert portfolio.status_code == 200
    assert "positions" in portfolio.json()

    templates = client.get("/api/templates")
    assert templates.status_code == 200
    assert len(templates.json()) >= 3

    signals = client.get("/api/signals")
    assert signals.status_code == 200
    assert len(signals.json()) >= 3

    alerts = client.get("/api/alerts")
    assert alerts.status_code == 200
    assert isinstance(alerts.json(), list)

    cloned = client.post("/api/templates/grid-guarded-spot/clone")
    assert cloned.status_code == 200
    assert "Guarded Spot Grid" in cloned.json()["name"]


def test_airdrop_workspace_local_flow() -> None:
    dashboard = client.get("/api/airdrops")
    assert dashboard.status_code == 200
    payload = dashboard.json()
    assert payload["metrics"]["project_count"] >= 5
    assert payload["projects"][0]["summary"]["task_total"] >= 2

    somnia = client.post("/api/airdrops/somnia-quests/assist", json={"live": False})
    assert somnia.status_code == 200
    somnia_payload = somnia.json()
    assert somnia_payload["plan"]["project_id"] == "somnia-quests"
    assert somnia_payload["plan"]["status"] == "ready"
    assert somnia_payload["plan"]["manual_steps"]
    assert "半自动引导已生成" in somnia_payload["dashboard"]["activity_log"][0]["title"]

    metamask = client.post("/api/airdrops/metamask-rewards/assist", json={"live": False})
    assert metamask.status_code == 200
    metamask_payload = metamask.json()
    assert metamask_payload["plan"]["project_id"] == "metamask-rewards"
    assert metamask_payload["plan"]["status"] in {"ended", "manual_only"}
    assert metamask_payload["plan"]["primary_action"]["url"]

    custom = client.post(
        "/api/airdrops/projects",
        json={
            "name": "Unit Test Airdrop",
            "chain": "Testnet",
            "category": "Quest",
            "official_url": "https://example.com/airdrop",
            "priority": "low",
            "risk_level": "low",
            "notes": "unit test",
        },
    )
    assert custom.status_code == 200
    project = custom.json()
    assert project["name"] == "Unit Test Airdrop"
    assert project["tasks"][0]["status"] == "todo"

    task_id = project["tasks"][0]["id"]
    updated = client.put(
        f"/api/airdrops/projects/{project['id']}/tasks/{task_id}",
        json={"status": "done", "evidence": "checked official page", "tx_hash": "", "cost_usd": 1.25},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"
    assert updated.json()["cost_usd"] == 1.25

    refreshed = client.post("/api/airdrops/refresh", json={"live": False})
    assert refreshed.status_code == 200
    assert refreshed.json()["last_refresh_at"]


def test_live_exchange_readiness_without_real_network() -> None:
    status = client.get("/api/live/status")
    assert status.status_code == 200
    assert "okx" in status.json()["accounts"]

    config = client.post("/api/live/configs/okx")
    assert config.status_code == 200
    assert config.json()["exchange"] == "okx"

    connected = client.post(
        "/api/live/accounts/connect",
        json={
            "exchange": "okx",
            "api_key": "test_key_1234",
            "api_secret": "test_secret_1234",
            "passphrase": "test_passphrase",
            "label": "unit-test",
            "test_connection": False,
            "save_to_env": False,
            "generate_live_config": True,
        },
    )
    assert connected.status_code == 200
    assert connected.json()["status"] == "saved_without_network_test"

    denied = client.post("/api/live/start", json={"exchange": "okx", "ack": "wrong"})
    assert denied.status_code == 400


def test_live_order_preview_and_submission_guards() -> None:
    preview = client.post(
        "/api/live/orders/preview",
        json={
            "exchange": "okx",
            "pair": "BTC/USDT",
            "side": "buy",
            "order_type": "limit",
            "quote_amount": 10,
            "price": 50000,
        },
    )
    assert preview.status_code == 200
    assert preview.json()["passed"] is True
    assert preview.json()["base_amount_estimate"] > 0

    missing_price = client.post(
        "/api/live/orders/preview",
        json={
            "exchange": "okx",
            "pair": "BTC/USDT",
            "side": "buy",
            "order_type": "limit",
            "quote_amount": 10,
        },
    )
    assert missing_price.status_code == 200
    assert missing_price.json()["passed"] is False

    denied = client.post(
        "/api/live/orders",
        json={
            "exchange": "okx",
            "pair": "BTC/USDT",
            "side": "buy",
            "order_type": "limit",
            "quote_amount": 10,
            "price": 50000,
            "ack": "wrong",
        },
    )
    assert denied.status_code == 400


def test_live_order_management_guards_without_real_network() -> None:
    refresh = client.post("/api/live/accounts/okx/refresh")
    assert refresh.status_code == 400
    assert "credentials are missing" in refresh.text

    open_orders = client.get("/api/live/orders/open?exchange=okx&pair=BTC/USDT")
    assert open_orders.status_code == 400
    assert "must be connected" in open_orders.text

    bad_pair = client.get("/api/live/orders/open?exchange=okx&pair=DOGE/USDT")
    assert bad_pair.status_code == 400
    assert "allowed_pairs" in bad_pair.text

    cancel_denied = client.post(
        "/api/live/orders/cancel",
        json={
            "exchange": "okx",
            "pair": "BTC/USDT",
            "order_id": "123",
            "client_order_id": "",
            "ack": "wrong",
        },
    )
    assert cancel_denied.status_code == 400
    assert "exact acknowledgement" in cancel_denied.text
