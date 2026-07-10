# Crypto Bot Platform

单人本地币圈 Bot 操作台，参考 3Commas、Bitsgap、Cryptohopper、Coinrule 一类产品的核心工作流。当前已支持本机 `freqtrade-agent` 的 OKX/Binance dry-run，以及 OKX/Binance 真实 API 账号接入、验权、余额刷新、live 配置生成、实盘启动前预检、手动现货下单、未成交/历史订单查询和撤单。

## 安全边界

- 只服务本机单用户。
- 默认仍建议先做 OKX 现货 dry-run。
- 真实账号接入仅支持 API Key 方式，不接收交易所网页登录密码。
- API Key 只允许读取和现货交易权限，必须关闭提现权限。
- 禁止合约、杠杆、做空。
- live profile 启动必须通过预检，并输入确认文字：`我确认这是实盘交易并愿意承担风险`。
- Freqtrade WebUI 和本平台都只建议绑定 `127.0.0.1`。
- 后端只对白名单命令放行：`setup`、数据下载、回测、dry-run 启停、停止；live 启动只能走 `/api/live/start` 的预检路径。

## 本地启动

首次安装依赖：

```bash
cd crypto-bot-platform
make setup
```

后端：

```bash
cd crypto-bot-platform
make backend
```

前端：

```bash
cd crypto-bot-platform
make frontend
```

访问：

- 产品操作台：`http://127.0.0.1:5175`
- 后端 API：`http://127.0.0.1:8011/api/overview`
- Freqtrade OKX WebUI：`http://127.0.0.1:8081`
- Freqtrade OKX live WebUI：`http://127.0.0.1:8091`
- Freqtrade Binance live WebUI：`http://127.0.0.1:8090`

## 已覆盖的产品能力

- 仪表盘：Bot 状态、风控状态、最近回测、产品完成矩阵。
- Bot 控制：OKX/Binance dry-run 白名单命令、Docker 状态、API ping、日志。
- 交易所接入：OKX/Binance API Key 验权、余额读取、权限检查、本地私有 env 保存。
- Live 配置：生成 `config_spot_live_okx.example.json`、`config_spot_live_binance.example.json`；连接并选择保存后生成 `.local.json`。
- Live 预检：检查账号已连接、无提现权限、有交易权限、本地配置和 env 存在。
- 手动现货下单：支持 OKX/Binance 白名单交易对订单预览和真实订单提交；真实提交必须通过预检并输入确认文字。
- 订单管理：用已保存的本机 env 刷新余额/权限，查询交易所未成交订单、近期订单，并通过确认文字撤单。
- 资产视图：读取 dry-run SQLite，展示 paper wallet、持仓占用、可用估算、open positions。
- 空投工作区：项目库、官方实时源刷新、任务清单、钱包标签、成本收益、证据日志。
- 模板中心：内置 Grid、DCA、Signal 三类 Bot 模板，可生成策略草稿。
- 策略实验室：规则草稿、交易对、进出场条件、风险备注。
- 信号中心：本地推导风控/策略/运行状态信号，只做观察建议。
- 回测中心：读取现有 Freqtrade 回测压缩包，展示收益、胜率、回撤、连续亏损。
- 风控中心：仓位、回撤、连续亏损、禁止事项与本地配置。
- 市场观察：OKX watchlist 与交易对角色。
- 告警与日志：回撤、连续亏损、主 Bot 运行状态告警，后台命令任务状态与输出尾部。

## 空投工作区

访问产品操作台后进入 `空投` 页面：

- `刷新全部` 会请求项目的官方页面、文档或任务页，更新在线状态、关键词信号和内容变更记录。
- 项目默认包含 MetaMask Rewards、Lighter Points、Somnia Quests、Grass Rewards、Eclipse Season Watch。
- 可以手动新增项目，填写官方入口后会自动生成研究、风险检查、证据记录三条任务。
- 每条任务可以记录状态、tx hash、截图/链接/备注和成本，平台会汇总项目与全局投入。
- 钱包标签只保存用途和备注；不保存助记词、私钥或浏览器钱包登录状态。

后端接口：

- `GET /api/airdrops`
- `POST /api/airdrops/refresh`
- `POST /api/airdrops/projects`
- `PUT /api/airdrops/projects/{project_id}/tasks/{task_id}`
- `POST /api/airdrops/wallets`

## 真实账号接入流程

1. 在 OKX/Binance 创建 API Key。
2. 权限只开启读取和现货交易，关闭提现；建议绑定当前机器公网 IP。
3. 打开产品操作台的 `交易所` 页面。
4. 粘贴 API Key / Secret；OKX 还需要 Passphrase。
5. 勾选 `立刻请求交易所，验证权限并读取余额`。
6. 勾选 `保存到本机私有 .env.live.local 与 .local.json`。
7. 点击 `连接并验权`。
8. 预检全部通过后，输入确认文字，再启动对应 live profile。
9. 后续可直接点击 `刷新余额`，从已保存的本机 env 重新读取余额与权限。
10. 如需手动下单，在 `手动现货下单` 区域先预览订单，再输入确认文字提交。
11. 如需管理订单，在 `实盘订单管理` 区域查询未成交/近期订单；撤单前仍需输入确认文字。

本地私有文件：

- `freqtrade-agent/.env.live.local`
- `freqtrade-agent/user_data/config_spot_live_okx.local.json`
- `freqtrade-agent/user_data/config_spot_live_binance.local.json`

这些文件已加入 `.gitignore`。不要分享它们。

手动真实下单默认限制：

- 只支持 `BTC/USDT`、`ETH/USDT`、`SOL/USDT`
- 单笔 `quote_amount <= 10 USDT`
- 限价单会按 `quote_amount / price` 估算基础币数量
- 市价单仅开放买入，避免卖出基础币数量歧义
- 提交前必须输入：`我确认这是实盘交易并愿意承担风险`
- 撤单前同样必须输入：`我确认这是实盘交易并愿意承担风险`

## 验证

```bash
cd crypto-bot-platform
make test
```
