# Risk Rules

当前阶段：现货 dry-run。禁止实盘、禁止合约、禁止杠杆、禁止做空。

## 仓位限制

- 单笔 `stake_amount` 不超过 50 USDT。
- `max_open_trades` 不超过 3。
- 只交易 `BTC/USDT`、`ETH/USDT`、`SOL/USDT`。
- 第一阶段禁止使用杠杆。

## 止损与暂停

- 单笔止损为 -5%。
- 日内亏损超过 -5% 停止。
- 总回撤超过 -10% 暂停观察。
- 总回撤超过 -20% 停止策略。
- 连续亏损 3 笔暂停。
- API 报错暂停。
- 网络断线暂停。

## API 权限

- 交易所 API 只允许开交易权限。
- 禁止开启提现权限。
- API Key 不写入代码或 JSON。
- 第一阶段 dry-run 不需要真实 API Key。

