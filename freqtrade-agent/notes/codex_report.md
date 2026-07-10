# Codex Report

生成时间：2026-05-28 00:40 Asia/Shanghai（Docker 日志时间为 2026-05-27 16:40 UTC），环境：Mac 本地 Docker，Freqtrade 镜像 `freqtradeorg/freqtrade:stable`，运行版本 `freqtrade 2026.4`。

## 1. 已创建哪些文件

- `docker-compose.yml`
- `.env.example`
- `.gitignore`
- `README.md`
- `Makefile`
- `tools/local_api_proxy.py`
- `user_data/config_spot_dryrun_binance.json`
- `user_data/config_spot_dryrun_okx.json`
- `user_data/strategies/HybridSafeStrategy.py`
- `user_data/data/`
- `user_data/logs/`
- `user_data/backtest_results/`
- `notes/runbook.md`
- `notes/risk_rules.md`
- `notes/codex_report.md`

没有创建 live 实盘配置；没有创建合约配置；没有创建 AI 自动下单模块。

## 2. 哪些命令可以运行

- `make setup`
- `make download-binance`
- `make download-okx`
- `make backtest-binance`
- `make backtest-okx`
- `make dryrun-binance`
- `make dryrun-okx`
- `make stop`
- `make logs`

## 3. 是否成功下载数据

成功。

- Binance：`BTC/USDT`、`ETH/USDT`、`SOL/USDT` 的 `15m` 和 `1h` 数据已下载。
- OKX：`BTC/USDT`、`ETH/USDT`、`SOL/USDT` 的 `15m` 和 `1h` 数据已下载。
- 数据范围：从 `2025-11-28 00:00:00` 到 `2026-05-27 16:00:00` 附近，约 180 天。
- 每个交易所每个交易对下载量：`15m` 约 17345 根，`1h` 约 4336 根。

## 4. 是否成功完成回测

成功。回测周期为 `15m`，交易模式为现货，最大同时开仓数为 3，单笔 stake 为 50 USDT。

### Binance 回测结果

- 总收益：`-103.799 USDT`
- 总收益率：`-10.38%`
- 胜率：`34.2%`
- 最大回撤：`104.491 USDT / 10.44%`
- 交易次数：`1092`
- 平均持仓时间：`3:22:00`
- 最大连续亏损：`31`

### OKX 回测结果

- 总收益：`-152.754 USDT`
- 总收益率：`-15.28%`
- 胜率：`32.1%`
- 最大回撤：`152.754 USDT / 15.28%`
- 交易次数：`1112`
- 平均持仓时间：`3:20:00`
- 最大连续亏损：`31`

## 5. 最大回撤是多少

- Binance：`10.44%`
- OKX：`15.28%`

两者均未超过硬阈值 `20%`。但 OKX 已超过风控文档中的 `总回撤超过 -10% 暂停观察` 阈值，Binance 也略高于 `10%`。

## 6. 是否可以进入 dry-run

可以进入现货 dry-run。

已验证：

- `dry_run: true`
- `trading_mode: spot`
- `can_short = False`
- `max_open_trades: 3`
- `stake_amount: 50`
- `api_server.listen_ip_address: 127.0.0.1`
- Binance WebUI：`http://127.0.0.1:8080`
- OKX WebUI：`http://127.0.0.1:8081`
- `/api/v1/ping` 返回 `{"status":"pong"}`
- 启动日志包含 `Dry run is enabled` 和 `Changing state to: RUNNING`

## 7. 是否有任何报错

最终版本无阻断报错。

修复过的问题：

- 初始配置缺少当前 Freqtrade 需要的 `entry_pricing` / `exit_pricing`，已补齐。
- 初始 `make stop` 没有覆盖 profile 容器，已改为同时处理 `binance` 和 `okx` profile。
- Freqtrade 容器内严格监听 `127.0.0.1` 时，Docker 端口代理无法直接访问；已增加 `tools/local_api_proxy.py`，保持 Freqtrade API server 监听 `127.0.0.1:8080`，宿主机也只发布到 `127.0.0.1`。
- `--export-filename` 在 Freqtrade 2026.4 中已弃用，已改为 `--backtest-directory`。

## 8. 下一步建议

不建议进入实盘阶段。

原因：

- Binance 和 OKX 回测总收益均为负。
- 两边最大连续亏损均达到 31 笔，已经超过 `连续亏损 3 笔暂停` 的风控要求。
- OKX 最大回撤 `15.28%`，超过 `-10% 暂停观察` 阈值。

下一步只建议做 dry-run 观察和策略改良：

1. 先运行 `make dryrun-binance` 或 `make dryrun-okx`，只做模拟。
2. 每日检查日志、回撤、连续亏损和异常。
3. 调整策略过滤条件后重新回测，例如增加大周期趋势过滤、降低交易频率、优化出场条件。
4. 不要进入实盘，不要使用合约，不要开启杠杆，不要让 AI 自动下单。
