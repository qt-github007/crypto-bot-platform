# Crypto Bot Platform

面向单用户、本地运行的加密货币交易与研究操作台。项目参考 3Commas、Bitsgap、Cryptohopper、Coinrule 等产品的核心工作流，把账户接入、dry-run、回测、策略、风控、资产与空投研究集中到一个界面中。

> 本项目用于技术研究和交易流程管理，不构成投资建议。默认使用 dry-run；接入实盘前请独立审查代码、交易所权限和风险参数。

## 仓库结构

- `crypto-bot-platform/`：FastAPI 后端与 React/Vite 操作台。
- `freqtrade-agent/`：Freqtrade 策略、Docker profiles、dry-run 与受控 live 运行层。

两个目录需要保持同级，操作台会通过本地白名单命令调用 `freqtrade-agent`。

## 快速开始

需要 Python 3、Node.js、npm，以及运行交易 Agent 时所需的 Docker Desktop。

```bash
cd crypto-bot-platform
make setup
make test
```

分别启动后端和前端：

```bash
cd crypto-bot-platform
make backend
```

```bash
cd crypto-bot-platform
make frontend
```

打开 `http://127.0.0.1:5175`。

Freqtrade 的初始化、数据下载、回测和 dry-run 操作见 [`freqtrade-agent/README.md`](freqtrade-agent/README.md)。

## 安全边界

- API Key 只应开启读取和现货交易权限，严禁提现权限。
- `.env`、本地 live 配置、数据库、行情和回测结果均被 Git 忽略。
- 默认只支持现货，禁止杠杆、合约、做空。
- 实盘启动与真实订单提交必须通过预检和人工确认。
- Web 服务默认仅绑定 `127.0.0.1`。
- 不保存助记词、私钥或交易所网页登录密码。

公开部署前请自行增加认证、HTTPS、密钥管理和更严格的网络隔离。本项目当前设计目标是本机单用户使用，不应直接暴露到公网。

## 详细文档

- [操作台说明](crypto-bot-platform/README.md)
- [Freqtrade Agent 说明](freqtrade-agent/README.md)
- [风险规则](freqtrade-agent/notes/risk_rules.md)
- [运行手册](freqtrade-agent/notes/runbook.md)

