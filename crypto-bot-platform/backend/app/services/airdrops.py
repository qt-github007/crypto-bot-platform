from __future__ import annotations

import hashlib
import html
import re
from copy import deepcopy
from typing import Any, Optional
from uuid import uuid4

import httpx

from app.services.state import now, read_state, write_state

SIGNAL_KEYWORDS = {
    "airdrop": ["airdrop", "空投"],
    "claim": ["claim", "领取"],
    "points": ["point", "points", "积分"],
    "rewards": ["reward", "rewards", "奖励"],
    "quest": ["quest", "任务"],
    "season": ["season", "赛季"],
    "deadline": ["deadline", "snapshot", "截止", "快照"],
    "ended": ["ended", "closed", "结束"],
}


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def _page_title(text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S)
    return _normalize_text(match.group(1))[:160] if match else ""


def _plain_excerpt(text: str) -> str:
    cleaned = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.I | re.S)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    return _normalize_text(cleaned)[:420]


def _detect_signals(text: str) -> list[str]:
    lowered = text.lower()
    signals: list[str] = []
    for signal, keywords in SIGNAL_KEYWORDS.items():
        if any(_has_keyword(lowered, keyword.lower()) for keyword in keywords):
            signals.append(signal)
    return signals


def _has_keyword(text: str, keyword: str) -> bool:
    if any(ord(char) > 127 for char in keyword):
        return keyword in text
    return bool(re.search(rf"\b{re.escape(keyword)}\b", text))


def _source_hash(text: str) -> str:
    normalized = _normalize_text(re.sub(r"<[^>]+>", " ", text)).lower()
    return hashlib.sha1(normalized[:50000].encode("utf-8", errors="ignore")).hexdigest()


def _fetch_source(client: httpx.Client, source: dict[str, Any]) -> dict[str, Any]:
    checked_at = now()
    url = source["url"]
    try:
        response = client.get(
            url,
            headers={
                "User-Agent": "CryptoConsoleAirdropMonitor/0.1 (+local single-user dashboard)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        text = response.text[:120000]
        ok = response.status_code < 400
        return {
            "label": source.get("label", url),
            "url": url,
            "kind": source.get("kind", "official"),
            "ok": ok,
            "status_code": response.status_code,
            "checked_at": checked_at,
            "title": _page_title(text),
            "snippet": _plain_excerpt(text),
            "signals": _detect_signals(text),
            "content_hash": _source_hash(text) if ok else "",
            "error": "",
        }
    except Exception as exc:
        return {
            "label": source.get("label", url),
            "url": url,
            "kind": source.get("kind", "official"),
            "ok": False,
            "status_code": None,
            "checked_at": checked_at,
            "title": "",
            "snippet": "",
            "signals": [],
            "content_hash": "",
            "error": str(exc)[:300],
        }


def _project_summary(project: dict[str, Any]) -> dict[str, Any]:
    tasks = project.get("tasks", [])
    source_results = project.get("source_results", [])
    total_cost = sum(float(task.get("cost_usd") or 0) for task in tasks)
    done = len([task for task in tasks if task.get("status") == "done"])
    todo = len([task for task in tasks if task.get("status") == "todo"])
    blocked = len([task for task in tasks if task.get("status") == "blocked"])
    return {
        "task_total": len(tasks),
        "task_done": done,
        "task_todo": todo,
        "task_blocked": blocked,
        "total_cost_usd": round(total_cost, 4),
        "official_sources": len(project.get("sources", [])),
        "online_sources": len([source for source in source_results if source.get("ok")]),
    }


def _dashboard_from_state(state: dict[str, Any]) -> dict[str, Any]:
    workspace = deepcopy(state["airdrop_workspace"])
    projects = workspace.get("projects", [])
    for project in projects:
        project["summary"] = _project_summary(project)

    total_cost = sum(project["summary"]["total_cost_usd"] for project in projects)
    active_count = len([project for project in projects if project.get("status") == "active"])
    high_priority_count = len([project for project in projects if project.get("priority") == "high"])
    checked_count = len([project for project in projects if project.get("source_health") != "not_checked"])
    return {
        "settings": workspace.get("settings", {}),
        "last_refresh_at": workspace.get("last_refresh_at"),
        "wallets": workspace.get("wallets", []),
        "projects": projects,
        "activity_log": workspace.get("activity_log", [])[:60],
        "metrics": {
            "project_count": len(projects),
            "active_count": active_count,
            "high_priority_count": high_priority_count,
            "checked_count": checked_count,
            "total_cost_usd": round(total_cost, 4),
        },
    }


def get_airdrop_dashboard() -> dict[str, Any]:
    return _dashboard_from_state(read_state())


def _find_project(state: dict[str, Any], project_id: str) -> dict[str, Any]:
    for project in state["airdrop_workspace"].get("projects", []):
        if project.get("id") == project_id:
            return deepcopy(project)
    raise ValueError("Airdrop project not found")


def _project_text_blob(project: dict[str, Any]) -> str:
    chunks = [project.get("name", ""), project.get("notes", "")]
    for source in project.get("source_results", []):
        chunks.extend([source.get("title", ""), source.get("snippet", ""), " ".join(source.get("signals", []))])
    return " ".join(chunks).lower()


def _assistant_plan(project: dict[str, Any]) -> dict[str, Any]:
    blob = _project_text_blob(project)
    official_url = project.get("official_url")
    base_plan = {
        "project_id": project["id"],
        "project_name": project["name"],
        "status": "ready",
        "headline": "可以开始，但关键步骤仍需要你自己在钱包里确认。",
        "summary": "我会帮你刷新官网、识别当前阶段、整理步骤和风险点；连接钱包、签名、授权、发交易由你自己做。",
        "primary_action": {"label": "打开官网", "url": official_url},
        "auto_done": [
            "已刷新并核对官方入口",
            "已整理当前项目的建议步骤",
            "已拆分自动步骤和手动确认步骤",
        ],
        "manual_steps": [],
        "do_not_do": [
            "不要输入助记词或私钥",
            "不要用主钱包给陌生合约大额授权",
            "不要自成交、对刷量或批量伪装多号",
        ],
        "next_checkpoints": [],
    }

    if project["id"] == "metamask-rewards":
        if "ended" in blob or "claim window is closed" in blob or "第 一 季" in blob or "现已结束" in blob:
            base_plan.update(
                {
                    "status": "ended",
                    "headline": "MetaMask 这张旧奖励页已经结束，不要再按这个入口做。",
                    "summary": "Season 1 已结束；如果你还想参与 MetaMask，只能改看移动端 Rewards tab 里的当前 campaigns。",
                    "primary_action": {
                        "label": "查看当前 Campaign 说明",
                        "url": "https://support.metamask.io/trade/metamask-rewards/how-to-participate-in-rewards/",
                    },
                    "manual_steps": [
                        "不要再刷当前网页；它对应的老奖励季已经结束。",
                        "如果还想做 MetaMask，请在 MetaMask Mobile 打开 Rewards tab。",
                        "只参与当前仍在进行的 campaign，并先确认是否需要 opt-in。",
                    ],
                    "next_checkpoints": [
                        "确认活动没有结束",
                        "确认你做的是当前 campaign，不是旧 Season 1 页面",
                        "确认是否需要在移动端先 opt-in",
                    ],
                }
            )
            return base_plan
        base_plan.update(
            {
                "status": "manual_only",
                "headline": "MetaMask 奖励需要走移动端 Rewards tab，不是这个网页里点几下就行。",
                "summary": "我能帮你识别活动页，但真正参加要在 MetaMask Mobile 里完成。",
                "manual_steps": [
                    "打开 MetaMask Mobile。",
                    "进入 Rewards tab，查看当前 campaigns。",
                    "确认活动仍在进行并按要求 opt-in。",
                ],
                "next_checkpoints": ["确认当前 campaign 仍在进行", "确认交易/任务在 opt-in 之后再做"],
            }
        )
        return base_plan

    if project["id"] == "somnia-quests":
        base_plan.update(
            {
                "status": "ready",
                "headline": "Somnia 适合现在开做，先挑最简单的 Quest / Campaign。",
                "summary": "我已经帮你锁定官网入口；你只需要用交互钱包连接、做 1 到 2 个低成本任务，然后回来记证据。",
                "primary_action": {"label": "打开 Somnia Quest", "url": official_url},
                "manual_steps": [
                    "点击 Start Questing 或进入 Campaigns。",
                    "用小额交互钱包连接，不要用主钱包。",
                    "先挑 1 到 2 个最简单的任务做，比如社媒、试玩、生态交互。",
                    "完成后回到这个平台，记录 tx hash、截图路径和花费。",
                ],
                "next_checkpoints": [
                    "看到 Campaigns / Leaderboard 页面",
                    "钱包已连接但未做危险授权",
                    "至少完成 1 个任务并回填证据",
                ],
            }
        )
        return base_plan

    if project["id"] == "grass-rewards":
        base_plan.update(
            {
                "status": "ready",
                "headline": "Grass 更像挂机型参与，不是一直点按钮。",
                "summary": "先注册、安装官方应用或扩展、点击 Connect，然后看 uptime 和 rewards。",
                "primary_action": {"label": "打开 Grass App", "url": official_url},
                "manual_steps": [
                    "注册或登录 Grass。",
                    "安装官方应用或扩展，只在你接受的设备/网络环境里使用。",
                    "登录后点击 Connect，保持在线。",
                    "回到平台记录运行时长、积分变化和隐私风险备注。",
                ],
                "next_checkpoints": [
                    "已确认是官方应用/扩展",
                    "仪表盘里能看到 uptime 或 rewards",
                    "已记录设备与隐私风险",
                ],
            }
        )
        return base_plan

    if project["id"] == "lighter-points":
        base_plan.update(
            {
                "status": "advanced",
                "headline": "Lighter 只适合懂永续/合约的人，先读规则，再决定是否参与。",
                "summary": "这个不是签到型空投；主要是 points 规则和交易行为。新手建议只读文档，不急着下场。",
                "primary_action": {"label": "打开 Lighter 积分文档", "url": official_url},
                "manual_steps": [
                    "先完整阅读 Points Program 和 Retail 规则。",
                    "如果你不懂永续/合约，先不要做真实交易。",
                    "如果决定参与，只用小仓真实交易，不要自成交或故意做损。",
                ],
                "next_checkpoints": [
                    "读完积分规则",
                    "明确自己的最大手续费和最大亏损预算",
                    "只在完全理解风险后再做真实单",
                ],
            }
        )
        return base_plan

    if project["id"] == "eclipse-season-watch":
        base_plan.update(
            {
                "status": "watch",
                "headline": "Eclipse 现在更适合观察，不建议你把它当主线撸。",
                "summary": "先看公告有没有新赛季或新规则，再决定是否投入时间和 gas。",
                "primary_action": {"label": "查看 Eclipse 公告", "url": official_url},
                "manual_steps": [
                    "先看官方公告有没有新 season / claim / snapshot。",
                    "没有明确活动时，不要盲目做高成本交互。",
                ],
                "next_checkpoints": ["出现明确的新活动或新赛季再回来做", "先保持观察即可"],
            }
        )
        return base_plan

    base_plan.update(
        {
            "manual_steps": [
                "先打开官方入口，确认这是真正的项目官网。",
                "阅读规则、截止时间和资格条件。",
                "只用小额交互钱包做最简单的真实任务。",
                "做完后回到平台记录证据和成本。",
            ],
            "next_checkpoints": ["确认官方入口", "确认活动没结束", "回填证据"],
        }
    )
    return base_plan


def assist_airdrop(project_id: str, live: bool = True) -> dict[str, Any]:
    if live:
        refresh_airdrop_sources(project_id=project_id, live=True)

    state = read_state()
    project = _find_project(state, project_id)
    project["summary"] = _project_summary(project)
    plan = _assistant_plan(project)
    status_text = {
        "ready": "可开始",
        "ended": "已结束",
        "manual_only": "仅手动",
        "advanced": "进阶模式",
        "watch": "继续观察",
    }.get(plan["status"], plan["status"])
    next_step = (plan.get("manual_steps") or ["先打开官网确认规则。"])[0]
    checked_at = now()

    state["airdrop_workspace"].setdefault("activity_log", []).insert(
        0,
        {
            "id": f"airdrop-assist-{uuid4().hex[:8]}",
            "created_at": checked_at,
            "title": f"半自动引导已生成：{project['name']}",
            "body": f"{'已刷新官方源并整理步骤' if live else '已按当前缓存整理步骤'}；结论：{status_text}。下一步：{next_step}",
            "severity": "warn" if plan["status"] in {"ended", "manual_only", "advanced"} else "info",
        },
    )
    state["airdrop_workspace"]["activity_log"] = state["airdrop_workspace"]["activity_log"][:120]
    write_state(state)
    return {"dashboard": get_airdrop_dashboard(), "plan": plan}


def refresh_airdrop_sources(project_id: Optional[str] = None, live: bool = True) -> dict[str, Any]:
    state = read_state()
    workspace = state["airdrop_workspace"]
    settings = workspace.get("settings", {})
    timeout = float(settings.get("source_timeout_seconds", 6))
    refreshed = 0
    changed_sources = 0
    checked_at = now()

    client_context = httpx.Client(timeout=timeout, follow_redirects=True) if live else None
    try:
        for project in workspace.get("projects", []):
            if project_id and project.get("id") != project_id:
                continue
            previous = {item.get("url"): item for item in project.get("source_results", [])}
            results = []
            signals: set[str] = set()
            if not live:
                for source in project.get("sources", []):
                    results.append(
                        {
                            "label": source.get("label", source["url"]),
                            "url": source["url"],
                            "kind": source.get("kind", "official"),
                            "ok": True,
                            "status_code": None,
                            "checked_at": checked_at,
                            "title": "offline refresh skipped",
                            "snippet": "Live network fetch was disabled for this refresh.",
                            "signals": [],
                            "content_hash": previous.get(source["url"], {}).get("content_hash", ""),
                            "error": "",
                        }
                    )
            else:
                assert client_context is not None
                for source in project.get("sources", []):
                    result = _fetch_source(client_context, source)
                    results.append(result)
                    signals.update(result.get("signals", []))
                    old_hash = previous.get(result["url"], {}).get("content_hash")
                    if result.get("content_hash") and old_hash and result["content_hash"] != old_hash:
                        changed_sources += 1

            ok_count = len([result for result in results if result.get("ok")])
            if ok_count == len(results) and results:
                source_health = "ok"
            elif ok_count:
                source_health = "partial"
            elif live:
                source_health = "error"
            else:
                source_health = "offline"

            project["source_results"] = results
            project["signals"] = sorted(signals)
            project["source_health"] = source_health
            project["last_checked_at"] = checked_at
            refreshed += 1
    finally:
        if client_context is not None:
            client_context.close()

    workspace["last_refresh_at"] = checked_at
    workspace.setdefault("activity_log", []).insert(
        0,
        {
            "id": f"airdrop-refresh-{uuid4().hex[:8]}",
            "created_at": checked_at,
            "title": "实时源刷新完成" if live else "离线刷新完成",
            "body": f"检查 {refreshed} 个项目；检测到 {changed_sources} 个官方源内容变化。",
            "severity": "info" if changed_sources == 0 else "warn",
        },
    )
    workspace["activity_log"] = workspace["activity_log"][:120]
    write_state(state)
    return get_airdrop_dashboard()


def create_airdrop_project(payload: dict[str, Any]) -> dict[str, Any]:
    state = read_state()
    workspace = state["airdrop_workspace"]
    project_id = payload.get("id") or re.sub(r"[^a-z0-9]+", "-", payload["name"].lower()).strip("-")[:48]
    if not project_id:
        project_id = f"project-{uuid4().hex[:8]}"
    existing_ids = {item.get("id") for item in workspace.get("projects", [])}
    if project_id in existing_ids:
        project_id = f"{project_id}-{uuid4().hex[:6]}"

    official_url = payload["official_url"]
    project = {
        "id": project_id,
        "name": payload["name"],
        "chain": payload.get("chain") or "Unknown",
        "category": payload.get("category") or "Custom",
        "status": payload.get("status") or "watch",
        "priority": payload.get("priority") or "medium",
        "stage": payload.get("stage") or "monitor",
        "risk_level": payload.get("risk_level") or "medium",
        "cost_level": payload.get("cost_level") or "unknown",
        "official_url": official_url,
        "notes": payload.get("notes") or "用户添加的项目，请先核对官方入口和授权风险。",
        "sources": [{"label": "Official", "url": official_url, "kind": "official"}],
        "tasks": [
            {"id": f"{project_id}-research", "title": "核对官方入口、规则和截止时间", "status": "todo", "kind": "research", "evidence": "", "tx_hash": "", "cost_usd": 0},
            {"id": f"{project_id}-risk", "title": "检查钱包授权、gas 预算和钓鱼风险", "status": "todo", "kind": "risk", "evidence": "", "tx_hash": "", "cost_usd": 0},
            {"id": f"{project_id}-proof", "title": "完成后记录 tx hash、截图路径或积分变化", "status": "todo", "kind": "evidence", "evidence": "", "tx_hash": "", "cost_usd": 0},
        ],
        "source_results": [],
        "signals": [],
        "last_checked_at": None,
        "source_health": "not_checked",
    }
    workspace.setdefault("projects", []).insert(0, project)
    workspace.setdefault("activity_log", []).insert(
        0,
        {
            "id": f"airdrop-add-{uuid4().hex[:8]}",
            "created_at": now(),
            "title": f"新增项目：{project['name']}",
            "body": official_url,
            "severity": "info",
        },
    )
    write_state(state)
    return project


def update_airdrop_task(project_id: str, task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    state = read_state()
    workspace = state["airdrop_workspace"]
    for project in workspace.get("projects", []):
        if project.get("id") != project_id:
            continue
        for task in project.get("tasks", []):
            if task.get("id") != task_id:
                continue
            if "status" in payload and payload["status"]:
                task["status"] = payload["status"]
            if "evidence" in payload:
                task["evidence"] = payload.get("evidence") or ""
            if "tx_hash" in payload:
                task["tx_hash"] = payload.get("tx_hash") or ""
            if "cost_usd" in payload and payload["cost_usd"] is not None:
                task["cost_usd"] = round(float(payload["cost_usd"]), 4)
            task["updated_at"] = now()
            workspace.setdefault("activity_log", []).insert(
                0,
                {
                    "id": f"airdrop-task-{uuid4().hex[:8]}",
                    "created_at": task["updated_at"],
                    "title": f"{project['name']} / {task['title']}",
                    "body": f"状态更新为 {task['status']}；成本 {task.get('cost_usd', 0)} USD。",
                    "severity": "info" if task["status"] == "done" else "warn" if task["status"] == "blocked" else "info",
                },
            )
            workspace["activity_log"] = workspace["activity_log"][:120]
            write_state(state)
            return task
    raise ValueError("Airdrop task not found")


def upsert_airdrop_wallet(payload: dict[str, Any]) -> dict[str, Any]:
    state = read_state()
    workspace = state["airdrop_workspace"]
    wallet_id = payload.get("id") or f"wallet-{uuid4().hex[:8]}"
    wallet = {
        "id": wallet_id,
        "label": payload["label"],
        "chains": payload.get("chains", []),
        "role": payload.get("role") or "airdrop tasks",
        "status": payload.get("status") or "ready",
        "notes": payload.get("notes") or "",
    }
    wallets = workspace.setdefault("wallets", [])
    for index, current in enumerate(wallets):
        if current.get("id") == wallet_id:
            wallets[index] = wallet
            write_state(state)
            return wallet
    wallets.insert(0, wallet)
    write_state(state)
    return wallet
