# Runbook

## 启动前检查

```bash
cd freqtrade-agent
make setup
```

确认 `.env` 存在，且没有填写提现权限相关 API。

## 下载数据

```bash
make download-binance
make download-okx
```

## 回测

```bash
make backtest-binance
make backtest-okx
```

回测后检查总收益、胜率、最大回撤、交易次数和平均持仓时间。最大回撤超过 20% 时，不建议进入实盘阶段。

## 启动 dry-run

Binance:

```bash
make dryrun-binance
```

OKX:

```bash
make dryrun-okx
```

## 停止

```bash
make stop
```

## 查看日志

```bash
make logs
```

重点检查：

- 是否打印 `Dry run is enabled` 或等价 dry-run 日志。
- 是否有 exchange API 报错。
- 是否有网络断线。
- 是否触发 stoploss 或连续亏损。

## 打开 WebUI

- Binance: `http://127.0.0.1:8080`
- OKX: `http://127.0.0.1:8081`

WebUI 只允许本机访问。配置中的 `api_server.listen_ip_address` 固定为 `127.0.0.1`。

Docker 映射同样只绑定宿主机 `127.0.0.1`。Binance 使用宿主机 `8080`，OKX 使用宿主机 `8081`。

## 切换 Binance / OKX

先停止当前实例：

```bash
make stop
```

再启动另一个交易所：

```bash
make dryrun-binance
```

或：

```bash
make dryrun-okx
```

## 检查 dry-run 是否没有真实下单

1. 检查配置文件中必须是 `"dry_run": true`。
2. 检查配置文件中必须是 `"trading_mode": "spot"`。
3. 检查配置文件中没有真实 API Key。
4. 检查日志中 dry-run 已启用。
5. 登录交易所账户，确认没有真实订单和资金变化。
6. 确认交易所 API 没有提现权限。

## 每日检查清单

- 查看 `make logs` 是否有 API、网络、数据库或策略异常。
- 检查 dry-run 盈亏、最大回撤和连续亏损次数。
- 日内亏损超过 -5% 时停止。
- 总回撤超过 -10% 时暂停观察。
- 总回撤超过 -20% 时停止策略。
- 连续亏损 3 笔时暂停。
- 不修改为 live，不开启合约，不开启杠杆。
