# Freqtrade Agent

本项目是在 Mac 本地运行的 Freqtrade 自动交易实验环境。默认路线仍是现货 dry-run；同时已经为本机单用户平台提供 OKX/Binance 现货 live profile 入口，实盘只能通过同级 `crypto-bot-platform` 的预检与确认流程启动。

## 安全边界

- 默认先运行 `dry_run: true`。
- 只做现货：`trading_mode: spot`。
- live 配置由平台生成，默认 `initial_state: stopped`、`stake_amount: 10`、`max_open_trades: 1`。
- API Key 不写入代码或 JSON，`.env.example` 只放占位符。
- 交易所 API 权限只允许开交易权限，禁止开启提现权限。
- WebUI 只允许绑定 `127.0.0.1`。
- 资金计划为 500-1000 USDT，默认单笔 `stake_amount` 为 50 USDT。

## 安装 Docker Desktop

1. 安装 Docker Desktop for Mac。
2. 启动 Docker Desktop，确认菜单栏 Docker 处于 Running。
3. 在终端确认：

```bash
docker --version
docker compose version
```

## 初始化

```bash
cd freqtrade-agent
make setup
```

`make setup` 会创建本地 `.env` 并拉取 `freqtradeorg/freqtrade:stable` 镜像。`.env` 只用于本机，不要提交。

## 下载数据

下载最近 180 天数据，交易对为 `BTC/USDT`、`ETH/USDT`、`SOL/USDT`，周期为 `15m` 和 `1h`。

```bash
make download-binance
make download-okx
```

## 回测

```bash
make backtest-binance
make backtest-okx
```

回测重点检查：

- 总收益
- 胜率
- 最大回撤
- 交易次数
- 平均持仓时间

如果最大回撤超过 20%，不建议进入实盘阶段。

## Dry-run

Binance:

```bash
make dryrun-binance
```

OKX:

```bash
make dryrun-okx
```

停止：

```bash
make stop
```

查看日志：

```bash
make logs
```

## Live profile

当前仓库已经具备 OKX/Binance 现货 live profile 的运行入口，但不要手工填写或提交 API Key。

推荐从同级 `crypto-bot-platform` 的 `交易所` 页面完成：

- API Key 验权
- 余额读取
- 提现权限检查
- `.env.live.local` 私有文件写入
- `config_spot_live_*.local.json` 私有配置生成
- live 启动前预检

live profile 的 Freqtrade 配置默认是：

- `dry_run: false`
- `trading_mode: spot`
- `initial_state: stopped`
- `stake_amount: 10`
- `max_open_trades: 1`

只有预检通过并输入确认文字后，平台才会调用：

```bash
make live-okx
make live-binance
```

## WebUI

- Binance dry-run: `http://127.0.0.1:8080`
- OKX dry-run: `http://127.0.0.1:8081`
- Binance live profile: `http://127.0.0.1:8090`
- OKX live profile: `http://127.0.0.1:8091`

默认用户名和密码在 `.env.example` 中只是本机 dry-run 占位符。首次运行前请复制为 `.env` 并修改。

Freqtrade 容器内 API server 固定监听 `127.0.0.1:8080`。Docker 对宿主机也只发布到 `127.0.0.1`，因此 WebUI 不会绑定到局域网地址。

## API Key 安全说明

Dry-run 不需要真实 API Key。使用 live profile 时：

- 只在 `.env` 中填写，不写进 JSON、Python 或 README。
- 交易所 API 只开启读取和现货交易权限。
- 严禁开启提现权限。
- 使用独立子账户或小资金账户。
- 实盘前必须重新审查配置、日志和风控结果。

## 后续 AI Agent 扩展

第三阶段可以加入 AI 情绪分析模块，但它只能输出观察信号、风险提示或人工审批建议。AI 不允许直接调用 Freqtrade 下单接口，不允许绕过策略风控，不允许修改 dry-run/live 状态。
