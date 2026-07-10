import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Activity,
  Bot,
  ChartCandlestick,
  ClipboardList,
  FileText,
  Gauge,
  Gift,
  History,
  LockKeyhole,
  KeyRound,
  CheckCircle2,
  ExternalLink,
  ListChecks,
  Play,
  Plus,
  PlugZap,
  RefreshCw,
  ScrollText,
  Settings,
  ShieldCheck,
  ShieldAlert,
  SlidersHorizontal,
  Square,
  TestTube2,
  Trash2,
  WalletCards,
  LayoutTemplate,
  RadioTower,
  BellRing
} from 'lucide-react'
import { api } from './api/client.js'
import MetricCard from './components/MetricCard.jsx'
import StatusPill from './components/StatusPill.jsx'
import Sparkline from './charts/Sparkline.jsx'
import { money, pct, shortText } from './store/format.js'
import { airdropStageText, categoryText, costLabel, riskLabel, taskKindText, uiText } from './store/uiText.js'

const nav = [
  { id: 'dashboard', label: '总览', icon: Activity },
  { id: 'bots', label: 'Bot', icon: Bot },
  { id: 'live', label: '交易所', icon: KeyRound },
  { id: 'portfolio', label: '资产', icon: WalletCards },
  { id: 'airdrops', label: '空投', icon: Gift },
  { id: 'templates', label: '模板', icon: LayoutTemplate },
  { id: 'strategy', label: '策略实验室', icon: SlidersHorizontal },
  { id: 'signals', label: '信号', icon: RadioTower },
  { id: 'backtests', label: '回测', icon: TestTube2 },
  { id: 'risk', label: '风控', icon: ShieldCheck },
  { id: 'market', label: '市场', icon: ChartCandlestick },
  { id: 'logs', label: '日志', icon: ScrollText },
  { id: 'settings', label: '设置', icon: Settings }
]

const actionLabels = {
  setup: '初始化',
  'download-okx': '下载 OKX 数据',
  'backtest-okx': 'OKX 回测',
  'dryrun-okx': '启动 OKX',
  'download-binance': '下载 Binance 数据',
  'backtest-binance': 'Binance 回测',
  'dryrun-binance': '启动 Binance',
  stop: '停止'
}

function orderStatusTone(status = '') {
  const normalized = String(status).toLowerCase()
  if (['live', 'partially_filled', 'new', 'submitted', 'open'].includes(normalized)) return 'warn'
  if (['filled', 'closed', 'canceled', 'cancelled'].includes(normalized)) return 'good'
  if (['rejected', 'expired', 'failed'].includes(normalized)) return 'danger'
  return 'neutral'
}

function useData() {
  const [overview, setOverview] = useState(null)
  const [bots, setBots] = useState([])
  const [backtests, setBacktests] = useState([])
  const [strategies, setStrategies] = useState([])
  const [portfolio, setPortfolio] = useState(null)
  const [signals, setSignals] = useState([])
  const [alerts, setAlerts] = useState([])
  const [templates, setTemplates] = useState([])
  const [liveStatus, setLiveStatus] = useState(null)
  const [liveOrders, setLiveOrders] = useState([])
  const [airdrops, setAirdrops] = useState(null)
  const [tasks, setTasks] = useState([])
  const [settings, setSettings] = useState(null)
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)

  async function refresh() {
    setBusy(true)
    try {
      const [overviewData, botsData, backtestsData, strategiesData, portfolioData, signalsData, alertsData, templatesData, liveStatusData, liveOrdersData, airdropsData, tasksData, settingsData] = await Promise.all([
        api.overview(),
        api.bots(),
        api.backtests(),
        api.strategies(),
        api.portfolio(),
        api.signals(),
        api.alerts(),
        api.templates(),
        api.liveStatus(),
        api.liveOrders(),
        api.airdrops(),
        api.tasks(),
        api.settings()
      ])
      setOverview(overviewData)
      setBots(botsData)
      setBacktests(backtestsData)
      setStrategies(strategiesData)
      setPortfolio(portfolioData)
      setSignals(signalsData)
      setAlerts(alertsData)
      setTemplates(templatesData)
      setLiveStatus(liveStatusData)
      setLiveOrders(liveOrdersData)
      setAirdrops(airdropsData)
      setTasks(tasksData)
      setSettings(settingsData)
    } catch (error) {
      setNotice(error.message)
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 15000)
    return () => clearInterval(id)
  }, [])

  return { overview, bots, backtests, strategies, portfolio, signals, alerts, templates, liveStatus, liveOrders, airdrops, setAirdrops, tasks, settings, notice, setNotice, busy, refresh, setStrategies }
}

export default function App() {
  const [page, setPage] = useState('dashboard')
  const data = useData()
  const current = nav.find((item) => item.id === page)

  async function runPrimaryAction(action) {
    const primary = data.bots.find((item) => item.id === 'okx_spot_dryrun')
    if (!primary) return
    try {
      const task = await api.botAction(primary.id, action)
      data.setNotice(`任务已进入队列：${actionLabels[action] || action} (${task.id.slice(0, 8)})`)
      await data.refresh()
    } catch (error) {
      data.setNotice(error.message)
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Gauge size={25} />
          <div>
            <strong>Crypto Console</strong>
            <span>OKX / Binance</span>
          </div>
        </div>
        <nav>
          {nav.map((item) => {
            const Icon = item.icon
            return (
              <button key={item.id} className={page === item.id ? 'active' : ''} onClick={() => setPage(item.id)} title={item.label}>
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            )
          })}
        </nav>
        <div className="side-lock">
          <LockKeyhole size={18} />
          <span>实盘启动需账号验权、禁提现、手动确认</span>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <h1>{current?.label}</h1>
            <span className="safety-line">单人本地版；现货 dry-run；真实账号接入需预检和手动确认</span>
          </div>
          <div className="top-actions">
            <button className="icon-button" onClick={data.refresh} title="刷新" disabled={data.busy}>
              <RefreshCw size={18} />
            </button>
            <button className="secondary-button" onClick={() => runPrimaryAction('backtest-okx')}>
              <TestTube2 size={18} />
              <span>回测</span>
            </button>
            <button className="primary-button" onClick={() => runPrimaryAction('dryrun-okx')}>
              <Play size={18} />
              <span>启动 OKX</span>
            </button>
            <button className="danger-button" onClick={() => runPrimaryAction('stop')}>
              <Square size={16} />
              <span>停止</span>
            </button>
          </div>
        </header>

        {data.notice ? (
          <div className="notice">
            <ClipboardList size={18} />
            <span>{data.notice}</span>
          </div>
        ) : null}

        {page === 'dashboard' ? <Dashboard {...data} /> : null}
        {page === 'bots' ? <BotsPage {...data} /> : null}
        {page === 'live' ? <LiveExchangePage {...data} /> : null}
        {page === 'portfolio' ? <PortfolioPage {...data} /> : null}
        {page === 'airdrops' ? <AirdropsPage {...data} /> : null}
        {page === 'templates' ? <TemplatesPage {...data} /> : null}
        {page === 'strategy' ? <StrategyPage {...data} /> : null}
        {page === 'signals' ? <SignalsPage {...data} /> : null}
        {page === 'backtests' ? <BacktestsPage {...data} /> : null}
        {page === 'risk' ? <RiskPage {...data} /> : null}
        {page === 'market' ? <MarketPage {...data} /> : null}
        {page === 'logs' ? <LogsPage {...data} /> : null}
        {page === 'settings' ? <SettingsPage {...data} /> : null}
      </main>
    </div>
  )
}

function Dashboard({ overview, bots, backtests, tasks, alerts }) {
  const primary = overview?.primary_bot
  const latest = overview?.last_okx_backtest || backtests[0]
  const openTrades = primary?.trades?.open_trades ?? 0
  const passedChecks = primary?.safety?.checks?.filter((item) => item.passed).length ?? 0
  const totalChecks = primary?.safety?.checks?.length ?? 0
  const scopedFeatures = overview?.feature_matrix?.filter((item) => item.status !== 'out_of_scope') || []
  const readyCount = scopedFeatures.filter((item) => item.status === 'ready' || item.status === 'locked').length
  const featureCount = scopedFeatures.length || 1

  return (
    <div className="page-stack">
      <section className="metric-grid four">
        <MetricCard label="主 Bot" value={uiText(primary?.runtime?.state || 'unknown')} helper="OKX 现货 Dry-run" tone={primary?.runtime?.state === 'running' ? 'good' : 'neutral'} />
        <MetricCard label="安全审计" value={`${passedChecks}/${totalChecks}`} helper="Dry-run / 现货 / 本地 / 无私钥" tone={primary?.safety?.passed ? 'good' : 'warn'} />
        <MetricCard label="模拟持仓" value={openTrades} helper={money(primary?.trades?.realized_profit || 0)} tone={openTrades ? 'warn' : 'neutral'} />
        <MetricCard label="功能完成" value={pct((readyCount / featureCount) * 100, 0)} helper="单人版核心能力" tone="good" />
      </section>

      <section className="dashboard-grid">
        <div className="panel hero-panel">
          <div className="panel-head">
            <div>
              <h2>OKX Dry-run 控制台</h2>
              <p>底层连接本机 Freqtrade，所有命令走后端白名单。</p>
            </div>
            <StatusPill value={uiText(overview?.safety?.live_trading || 'locked')} tone="danger" />
          </div>
          <div className="hero-metrics">
            <div>
              <small>最近 OKX 回测收益</small>
              <strong>{money(latest?.profit_abs || 0)}</strong>
              <span>{pct(latest?.profit_pct || 0)} / 胜率 {pct(latest?.winrate_pct || 0)}</span>
            </div>
            <Sparkline values={[1000, 986, 973, 964, 947, 930, 912, 895, 872, 847]} tone="red" />
          </div>
          <div className="warning-strip">
            历史 OKX 回测仍为负收益，连续亏损过高；当前产品只建议继续 dry-run 与策略改良。
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <h2>产品能力</h2>
            <StatusPill value={uiText('single user')} tone="good" />
          </div>
          <div className="feature-list">
            {(overview?.feature_matrix || []).map((item) => (
              <div key={item.name}>
                <span>{item.name}</span>
                <StatusPill value={item.status} tone={item.status === 'ready' ? 'good' : item.status === 'locked' ? 'danger' : 'neutral'} />
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>当前告警</h2>
          <StatusPill value={`${alerts?.length || 0} 条`} tone={alerts?.length ? 'warn' : 'good'} />
        </div>
        <div className="alert-grid">
          {(alerts || []).map((alert) => (
            <article key={alert.id}>
              <BellRing size={17} />
              <div>
                <strong>{alert.title}</strong>
                <span>{alert.detail}</span>
              </div>
            </article>
          ))}
          {!alerts?.length ? <p className="muted">暂无告警。</p> : null}
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Bot 概览</h2>
          <span>{bots.length} 个交易所配置</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>名称</th>
                <th>运行</th>
                <th>交易对</th>
                <th>Stake</th>
                <th>安全</th>
              </tr>
            </thead>
            <tbody>
              {bots.map((bot) => (
                <tr key={bot.id}>
                  <td>{bot.name}</td>
                  <td>{uiText(bot.runtime?.state)}</td>
                  <td>{bot.config_summary?.pairs?.join(', ')}</td>
                  <td>{money(bot.config_summary?.stake_amount || 0)}</td>
                  <td><StatusPill value={uiText(bot.safety?.passed ? 'passed' : 'review')} tone={bot.safety?.passed ? 'good' : 'warn'} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <TaskStrip tasks={tasks} />
    </div>
  )
}

function LiveExchangePage({ liveStatus, liveOrders, setNotice, refresh }) {
  const [form, setForm] = useState({
    exchange: 'okx',
    label: '',
    api_key: '',
    api_secret: '',
    passphrase: '',
    test_connection: true,
    save_to_env: true,
    generate_live_config: true
  })
  const [ack, setAck] = useState('')
  const [orderForm, setOrderForm] = useState({
    exchange: 'okx',
    pair: 'BTC/USDT',
    side: 'buy',
    order_type: 'limit',
    quote_amount: 10,
    price: '',
    ack: ''
  })
  const [orderPreview, setOrderPreview] = useState(null)
  const [orderQuery, setOrderQuery] = useState({ exchange: 'okx', pair: 'BTC/USDT' })
  const [openOrders, setOpenOrders] = useState(null)
  const [orderHistory, setOrderHistory] = useState(null)
  const [cancelForm, setCancelForm] = useState({ exchange: 'okx', pair: 'BTC/USDT', order_id: '', client_order_id: '', ack: '' })
  const accounts = liveStatus?.accounts || {}
  const selectedAccount = accounts[form.exchange] || {}
  const preflight = liveStatus?.preflight || { checks: [], passed: false }
  const requiredAck = liveStatus?.live_trading?.ack_required || '我确认这是实盘交易并愿意承担风险'

  async function connect(event) {
    event.preventDefault()
    try {
      const result = await api.connectExchange(form)
      setNotice(`${form.exchange.toUpperCase()} 接入完成：${result.status}`)
      setForm({ ...form, api_key: '', api_secret: '', passphrase: '' })
      await refresh()
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function refreshAccount(exchange) {
    try {
      const result = await api.refreshLiveAccount(exchange)
      setNotice(`${exchange.toUpperCase()} 余额与权限已刷新：${result.status}`)
      await refresh()
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function generate(exchange) {
    try {
      const result = await api.generateLiveConfig(exchange)
      setNotice(`已生成 ${exchange.toUpperCase()} live 示例配置：${result.path}`)
      await refresh()
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function startLive(exchange) {
    try {
      const result = await api.startLive({ exchange, ack })
      setNotice(`${exchange.toUpperCase()} live profile 已进入启动队列：${result.task.id.slice(0, 8)}`)
      setAck('')
      await refresh()
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function loadOpenOrders() {
    try {
      const result = await api.liveOpenOrders(orderQuery.exchange, orderQuery.pair)
      setOpenOrders(result)
      setNotice(`${orderQuery.exchange.toUpperCase()} 未成交订单 ${result.orders.length} 条`)
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function loadOrderHistory() {
    try {
      const result = await api.liveOrderHistory(orderQuery.exchange, orderQuery.pair)
      setOrderHistory(result)
      setNotice(`${orderQuery.exchange.toUpperCase()} 近期订单 ${result.orders.length} 条`)
    } catch (error) {
      setNotice(error.message)
    }
  }

  function prepareCancel(order) {
    setCancelForm({
      exchange: order.exchange,
      pair: order.pair || orderQuery.pair,
      order_id: order.order_id || '',
      client_order_id: order.client_order_id || '',
      ack: ''
    })
  }

  async function cancelOrder(event) {
    event.preventDefault()
    try {
      const result = await api.cancelLiveOrder(cancelForm)
      setNotice(`${result.exchange.toUpperCase()} 撤单请求已提交：${result.order_id || result.client_order_id}`)
      setCancelForm({ ...cancelForm, ack: '' })
      try {
        const refreshed = await api.liveOpenOrders(orderQuery.exchange, orderQuery.pair)
        setOpenOrders(refreshed)
      } catch {
        setOpenOrders(null)
      }
      await refresh()
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function previewOrder(event) {
    event.preventDefault()
    try {
      const payload = {
        ...orderForm,
        quote_amount: Number(orderForm.quote_amount),
        price: orderForm.price ? Number(orderForm.price) : null
      }
      const result = await api.previewLiveOrder(payload)
      setOrderPreview(result)
      setNotice(result.passed ? '订单预览通过本地规则' : `订单预览有问题：${result.issues.join('; ')}`)
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function submitOrder() {
    try {
      const payload = {
        ...orderForm,
        quote_amount: Number(orderForm.quote_amount),
        price: orderForm.price ? Number(orderForm.price) : null
      }
      const result = await api.submitLiveOrder(payload)
      setNotice(`真实订单已提交：${result.order.id.slice(0, 8)}`)
      setOrderForm({ ...orderForm, ack: '' })
      await refresh()
    } catch (error) {
      setNotice(error.message)
    }
  }

  return (
    <div className="page-stack">
      <section className="metric-grid four">
        <MetricCard label="OKX" value={uiText(accounts.okx?.status || 'not_connected')} helper={accounts.okx?.masked_api_key || '未接入'} tone={accounts.okx?.status === 'connected' ? 'good' : 'neutral'} />
        <MetricCard label="Binance" value={uiText(accounts.binance?.status || 'not_connected')} helper={accounts.binance?.masked_api_key || '未接入'} tone={accounts.binance?.status === 'connected' ? 'good' : 'neutral'} />
        <MetricCard label="实盘预检" value={uiText(preflight.passed ? 'passed' : 'blocked')} helper={`${preflight.checks?.filter((item) => item.passed).length || 0}/${preflight.checks?.length || 0} 项检查`} tone={preflight.passed ? 'good' : 'warn'} />
        <MetricCard label="密钥状态" value={uiText(liveStatus?.env_exists ? 'local env' : 'not saved')} helper={liveStatus?.env_path || ''} />
      </section>

      <div className="page-grid">
        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>交易所账号接入</h2>
              <p>粘贴 API Key 验证余额与权限；本地保存会写入私有 env/local config。</p>
            </div>
            <StatusPill value={uiText('real exchange api')} tone="warn" />
          </div>
          <form className="form-stack" onSubmit={connect}>
            <label>
              交易所
              <select value={form.exchange} onChange={(event) => setForm({ ...form, exchange: event.target.value })}>
                <option value="okx">OKX</option>
                <option value="binance">Binance</option>
              </select>
            </label>
            <label>
              标签
              <input value={form.label} onChange={(event) => setForm({ ...form, label: event.target.value })} placeholder="主账户 / 子账户" />
            </label>
            <label>
              API Key
              <input type="password" value={form.api_key} onChange={(event) => setForm({ ...form, api_key: event.target.value })} required />
            </label>
            <label>
              API Secret
              <input type="password" value={form.api_secret} onChange={(event) => setForm({ ...form, api_secret: event.target.value })} required />
            </label>
            {form.exchange === 'okx' ? (
              <label>
                OKX Passphrase
                <input type="password" value={form.passphrase} onChange={(event) => setForm({ ...form, passphrase: event.target.value })} required />
              </label>
            ) : null}
            <label className="check-row">
              <input type="checkbox" checked={form.test_connection} onChange={(event) => setForm({ ...form, test_connection: event.target.checked })} />
              <span>立刻请求交易所，验证权限并读取余额</span>
            </label>
            <label className="check-row">
              <input type="checkbox" checked={form.save_to_env} onChange={(event) => setForm({ ...form, save_to_env: event.target.checked })} />
              <span>保存到本机私有 `.env.live.local` 与 `.local.json`</span>
            </label>
            <label className="check-row">
              <input type="checkbox" checked={form.generate_live_config} onChange={(event) => setForm({ ...form, generate_live_config: event.target.checked })} />
              <span>生成 Freqtrade live 配置</span>
            </label>
            <button className="primary-button full" type="submit">
              <PlugZap size={17} />
              <span>连接并验权</span>
            </button>
          </form>
          <div className="warning-strip">
            API Key 只开读取和现货交易权限，必须关闭提现；建议绑定当前机器公网 IP。页面提交只发到本机后端。
          </div>
        </section>

        <section className="panel">
          <div className="panel-head">
            <h2>{form.exchange.toUpperCase()} 当前状态</h2>
            <div className="inline-actions">
              <button className="secondary-button small" type="button" onClick={() => refreshAccount(form.exchange)}>
                <RefreshCw size={15} />
                <span>刷新余额</span>
              </button>
              <StatusPill value={uiText(selectedAccount.status || 'not_connected')} tone={selectedAccount.status === 'connected' ? 'good' : selectedAccount.status === 'blocked' ? 'danger' : 'neutral'} />
            </div>
          </div>
          <dl className="kv-list">
            <dt>API Key</dt>
            <dd>{selectedAccount.masked_api_key || '-'}</dd>
            <dt>配置文件</dt>
            <dd>{selectedAccount.config_path || '-'}</dd>
            <dt>上次检查</dt>
            <dd>{selectedAccount.last_checked_at || '-'}</dd>
            <dt>保存本地</dt>
            <dd>{selectedAccount.saved_to_env ? 'yes' : 'no'}</dd>
          </dl>
          <div className="permission-grid">
            {Object.entries(selectedAccount.permissions || {}).map(([key, value]) => (
              <div key={key}>
                <span>{key}</span>
                <strong>{String(value || false)}</strong>
              </div>
            ))}
          </div>
          <div className="alert-list live-issues">
            {(selectedAccount.issues || []).map((issue) => (
              <article key={issue}>
                <StatusPill value={uiText('check')} tone={issue.toLowerCase().includes('withdraw') ? 'danger' : 'warn'} />
                <div><strong>{issue}</strong></div>
              </article>
            ))}
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>币种</th>
                  <th>可用</th>
                  <th>总额</th>
                </tr>
              </thead>
              <tbody>
                {(selectedAccount.balances || []).map((item) => (
                  <tr key={item.currency}>
                    <td>{item.currency}</td>
                    <td>{item.free}</td>
                    <td>{item.total}</td>
                  </tr>
                ))}
                {!selectedAccount.balances?.length ? <tr><td colSpan="3">暂无余额数据。</td></tr> : null}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>实盘启动前检查</h2>
            <p>只有全部通过，并输入确认文字，才会调用 Freqtrade live profile。</p>
          </div>
          <StatusPill value={uiText(preflight.passed ? 'passed' : 'blocked')} tone={preflight.passed ? 'good' : 'danger'} />
        </div>
        <div className="preflight-grid">
          {(preflight.checks || []).map((check) => (
            <div key={`${check.exchange}-${check.code}`}>
              <StatusPill value={uiText(check.passed ? 'OK' : 'NO')} tone={check.passed ? 'good' : 'danger'} />
              <strong>{check.exchange.toUpperCase()} / {check.code}</strong>
              <span>{check.message}</span>
            </div>
          ))}
        </div>
        <div className="inline-actions live-actions">
          <button className="secondary-button" onClick={() => generate('okx')}>生成 OKX 示例配置</button>
          <button className="secondary-button" onClick={() => generate('binance')}>生成 Binance 示例配置</button>
        </div>
        <div className="live-start-box">
          <label>
            启动确认文字
            <input value={ack} onChange={(event) => setAck(event.target.value)} placeholder={requiredAck} />
          </label>
          <div className="inline-actions">
            <button className="danger-button" onClick={() => startLive('okx')}>启动 OKX Live Profile</button>
            <button className="danger-button" onClick={() => startLive('binance')}>启动 Binance Live Profile</button>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>实盘订单管理</h2>
            <p>读取交易所未成交与近期订单；撤单需要再次输入确认文字。</p>
          </div>
          <StatusPill value={uiText('read / cancel')} tone="warn" />
        </div>
        <div className="order-management-grid">
          <label>
            交易所
            <select value={orderQuery.exchange} onChange={(event) => setOrderQuery({ ...orderQuery, exchange: event.target.value })}>
              <option value="okx">OKX</option>
              <option value="binance">Binance</option>
            </select>
          </label>
          <label>
            交易对
            <select value={orderQuery.pair} onChange={(event) => setOrderQuery({ ...orderQuery, pair: event.target.value })}>
              <option value="BTC/USDT">BTC/USDT</option>
              <option value="ETH/USDT">ETH/USDT</option>
              <option value="SOL/USDT">SOL/USDT</option>
            </select>
          </label>
          <button className="secondary-button" type="button" onClick={loadOpenOrders}>
            <RefreshCw size={16} />
            <span>查未成交</span>
          </button>
          <button className="secondary-button" type="button" onClick={loadOrderHistory}>
            <History size={16} />
            <span>查近期订单</span>
          </button>
        </div>

        <div className="order-books">
          <div>
            <div className="compact-head panel-head">
              <h3>未成交订单</h3>
              <StatusPill value={`${openOrders?.orders?.length || 0} 条`} tone={openOrders?.orders?.length ? 'warn' : 'neutral'} />
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>更新时间</th>
                    <th>订单号</th>
                    <th>方向</th>
                    <th>类型</th>
                    <th>价格</th>
                    <th>数量</th>
                    <th>成交</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {(openOrders?.orders || []).map((order) => (
                    <tr key={`${order.exchange}-${order.order_id || order.client_order_id}`}>
                      <td>{order.updated_at || order.created_at || '-'}</td>
                      <td className="mono-cell">{shortText(order.order_id || order.client_order_id, 22)}</td>
                      <td>{order.side}</td>
                      <td>{order.order_type}</td>
                      <td>{order.price || '-'}</td>
                      <td>{order.amount || '-'}</td>
                      <td>{order.filled || '-'}</td>
                      <td><StatusPill value={uiText(order.status || '-')} tone={orderStatusTone(order.status)} /></td>
                      <td>
                        <button className="danger-button small" type="button" onClick={() => prepareCancel(order)}>
                          <Trash2 size={14} />
                          <span>撤单</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                  {!openOrders?.orders?.length ? <tr><td colSpan="9">暂无未成交订单。</td></tr> : null}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <div className="compact-head panel-head">
              <h3>近期订单</h3>
              <StatusPill value={`${orderHistory?.orders?.length || 0} 条`} tone={orderHistory?.orders?.length ? 'good' : 'neutral'} />
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>时间</th>
                    <th>订单号</th>
                    <th>方向</th>
                    <th>类型</th>
                    <th>价格</th>
                    <th>数量</th>
                    <th>成交</th>
                    <th>状态</th>
                  </tr>
                </thead>
                <tbody>
                  {(orderHistory?.orders || []).map((order) => (
                    <tr key={`${order.exchange}-${order.order_id || order.client_order_id}`}>
                      <td>{order.updated_at || order.created_at || '-'}</td>
                      <td className="mono-cell">{shortText(order.order_id || order.client_order_id, 22)}</td>
                      <td>{order.side}</td>
                      <td>{order.order_type}</td>
                      <td>{order.price || '-'}</td>
                      <td>{order.amount || '-'}</td>
                      <td>{order.filled || '-'}</td>
                      <td><StatusPill value={uiText(order.status || '-')} tone={orderStatusTone(order.status)} /></td>
                    </tr>
                  ))}
                  {!orderHistory?.orders?.length ? <tr><td colSpan="8">暂无近期订单。</td></tr> : null}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <form className="cancel-grid" onSubmit={cancelOrder}>
          <label>
            交易所
            <select value={cancelForm.exchange} onChange={(event) => setCancelForm({ ...cancelForm, exchange: event.target.value })}>
              <option value="okx">OKX</option>
              <option value="binance">Binance</option>
            </select>
          </label>
          <label>
            交易对
            <select value={cancelForm.pair} onChange={(event) => setCancelForm({ ...cancelForm, pair: event.target.value })}>
              <option value="BTC/USDT">BTC/USDT</option>
              <option value="ETH/USDT">ETH/USDT</option>
              <option value="SOL/USDT">SOL/USDT</option>
            </select>
          </label>
          <label>
            订单号
            <input value={cancelForm.order_id} onChange={(event) => setCancelForm({ ...cancelForm, order_id: event.target.value })} placeholder="ordId / orderId" />
          </label>
          <label>
            Client ID
            <input value={cancelForm.client_order_id} onChange={(event) => setCancelForm({ ...cancelForm, client_order_id: event.target.value })} placeholder="clOrdId / clientOrderId" />
          </label>
          <label className="wide-field">
            撤单确认文字
            <input value={cancelForm.ack} onChange={(event) => setCancelForm({ ...cancelForm, ack: event.target.value })} placeholder={requiredAck} />
          </label>
          <button className="danger-button" type="submit">
            <Trash2 size={16} />
            <span>提交撤单</span>
          </button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>手动现货下单</h2>
            <p>先预览，再输入确认文字提交真实订单；仅支持现货白名单交易对。</p>
          </div>
          <StatusPill value={uiText('live order terminal')} tone="danger" />
        </div>
        <form className="order-grid" onSubmit={previewOrder}>
          <label>
            交易所
            <select value={orderForm.exchange} onChange={(event) => setOrderForm({ ...orderForm, exchange: event.target.value })}>
              <option value="okx">OKX</option>
              <option value="binance">Binance</option>
            </select>
          </label>
          <label>
            交易对
            <select value={orderForm.pair} onChange={(event) => setOrderForm({ ...orderForm, pair: event.target.value })}>
              <option value="BTC/USDT">BTC/USDT</option>
              <option value="ETH/USDT">ETH/USDT</option>
              <option value="SOL/USDT">SOL/USDT</option>
            </select>
          </label>
          <label>
            方向
            <select value={orderForm.side} onChange={(event) => setOrderForm({ ...orderForm, side: event.target.value })}>
              <option value="buy">买入</option>
              <option value="sell">卖出</option>
            </select>
          </label>
          <label>
            类型
            <select value={orderForm.order_type} onChange={(event) => setOrderForm({ ...orderForm, order_type: event.target.value })}>
              <option value="limit">限价</option>
              <option value="market">市价买入</option>
            </select>
          </label>
          <label>
            金额 USDT
            <input type="number" min="1" max="10" step="0.01" value={orderForm.quote_amount} onChange={(event) => setOrderForm({ ...orderForm, quote_amount: event.target.value })} />
          </label>
          <label>
            限价
            <input type="number" min="0" step="0.00000001" value={orderForm.price} onChange={(event) => setOrderForm({ ...orderForm, price: event.target.value })} disabled={orderForm.order_type === 'market'} />
          </label>
          <button className="secondary-button" type="submit">预览订单</button>
        </form>
        {orderPreview ? (
          <div className="order-preview">
            <MetricCard label="本地规则" value={uiText(orderPreview.passed ? 'passed' : 'blocked')} helper={orderPreview.issues?.join('; ') || '可进入提交前预检'} tone={orderPreview.passed ? 'good' : 'warn'} />
            <MetricCard label="估算基础币数量" value={orderPreview.base_amount_estimate ? Number(orderPreview.base_amount_estimate).toFixed(8) : '-'} helper={`${orderPreview.quote_amount} USDT`} />
            <MetricCard label="确认文字" value="required" helper={orderPreview.requires_ack} tone="warn" />
          </div>
        ) : null}
        <div className="live-start-box">
          <label>
            真实下单确认文字
            <input value={orderForm.ack} onChange={(event) => setOrderForm({ ...orderForm, ack: event.target.value })} placeholder={requiredAck} />
          </label>
          <button className="danger-button" onClick={submitOrder} type="button">提交真实订单</button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>时间</th>
                <th>交易所</th>
                <th>交易对</th>
                <th>方向</th>
                <th>类型</th>
                <th>金额</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              {(liveOrders || []).map((order) => (
                <tr key={order.id}>
                  <td>{order.created_at}</td>
                  <td>{order.exchange}</td>
                  <td>{order.pair}</td>
                  <td>{order.side}</td>
                  <td>{order.order_type}</td>
                  <td>{money(order.quote_amount)}</td>
                  <td>{order.status}</td>
                </tr>
              ))}
              {!liveOrders?.length ? <tr><td colSpan="7">暂无真实订单记录。</td></tr> : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

function PortfolioPage({ portfolio }) {
  const positions = portfolio?.positions || []
  return (
    <div className="page-stack">
      <section className="metric-grid four">
        <MetricCard label="Paper wallet" value={money(portfolio?.paper_wallet || 0)} helper="dry-run wallet" />
        <MetricCard label="已实现盈亏" value={money(portfolio?.realized_profit || 0)} tone={(portfolio?.realized_profit || 0) >= 0 ? 'good' : 'warn'} />
        <MetricCard label="持仓占用" value={money(portfolio?.open_exposure || 0)} helper={`${positions.length} open positions`} />
        <MetricCard label="可用估算" value={money(portfolio?.available_estimate || 0)} />
      </section>
      <section className="panel">
        <div className="panel-head">
          <h2>当前 dry-run 持仓</h2>
          <StatusPill value="read-only" tone="good" />
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Bot</th>
                <th>交易所</th>
                <th>交易对</th>
                <th>金额</th>
                <th>开仓价</th>
                <th>开仓时间</th>
                <th>策略</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((item, index) => (
                <tr key={`${item.bot_id}-${item.pair}-${index}`}>
                  <td>{item.bot_id}</td>
                  <td>{item.exchange}</td>
                  <td>{item.pair}</td>
                  <td>{money(item.stake_amount)}</td>
                  <td>{item.open_rate}</td>
                  <td>{item.open_date}</td>
                  <td>{item.strategy || '-'}</td>
                </tr>
              ))}
              {!positions.length ? (
                <tr><td colSpan="7">暂无 open dry-run 持仓。</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

function AirdropsPage({ airdrops, setAirdrops, setNotice, refresh }) {
  const projects = airdrops?.projects || []
  const metrics = airdrops?.metrics || {}
  const wallets = airdrops?.wallets || []
  const activityLog = airdrops?.activity_log || []
  const detailRef = useRef(null)
  const [selectedId, setSelectedId] = useState('')
  const [refreshing, setRefreshing] = useState(false)
  const [assisting, setAssisting] = useState(false)
  const [assistingProjectId, setAssistingProjectId] = useState('')
  const [assistantPlan, setAssistantPlan] = useState(null)
  const [newProject, setNewProject] = useState({
    name: '',
    chain: '',
    category: 'Quest',
    official_url: '',
    status: 'watch',
    priority: 'medium',
    stage: 'monitor',
    risk_level: 'medium',
    cost_level: 'low',
    notes: ''
  })
  const [taskForm, setTaskForm] = useState({
    task_id: '',
    status: 'done',
    evidence: '',
    tx_hash: '',
    cost_usd: 0
  })
  const [walletForm, setWalletForm] = useState({
    label: '',
    chains: 'EVM,Solana',
    role: '低额度交互',
    status: 'ready',
    notes: ''
  })

  useEffect(() => {
    if (!selectedId && projects[0]) setSelectedId(projects[0].id)
  }, [projects, selectedId])

  const selected = projects.find((project) => project.id === selectedId) || projects[0]

  useEffect(() => {
    const firstTask = selected?.tasks?.[0]
    if (firstTask) {
      setTaskForm({
        task_id: firstTask.id,
        status: firstTask.status === 'done' ? 'done' : 'done',
        evidence: firstTask.evidence || '',
        tx_hash: firstTask.tx_hash || '',
        cost_usd: firstTask.cost_usd || 0
      })
    }
  }, [selected?.id])

  function dateText(value) {
    if (!value) return '-'
    try {
      return new Date(value).toLocaleString('zh-CN', { hour12: false })
    } catch (_error) {
      return value
    }
  }

  function statusTone(value) {
    if (value === 'active' || value === 'ok' || value === 'done' || value === 'ready') return 'good'
    if (value === 'high' || value === 'blocked' || value === 'error') return 'danger'
    if (value === 'partial' || value === 'watch' || value === 'medium') return 'warn'
    return 'neutral'
  }

  async function refreshSources(projectId = '') {
    setRefreshing(true)
    try {
      const result = await api.refreshAirdrops({ project_id: projectId || null, live: true })
      setAirdrops(result)
      setNotice(`空投实时源已刷新：${result.metrics.checked_count}/${result.metrics.project_count} 个项目有检查结果`)
    } catch (error) {
      setNotice(error.message)
    } finally {
      setRefreshing(false)
    }
  }

  async function runAssist(project) {
    if (!project) return
    setAssisting(true)
    setAssistingProjectId(project.id)
    try {
      const result = await api.assistAirdrop(project.id, { live: true })
      setAirdrops(result.dashboard)
      setAssistantPlan(result.plan)
      setSelectedId(project.id)
      setNotice(`已整理 ${project.name} 的半自动引导，你只需要做关键确认步骤。`)
      window.requestAnimationFrame(() => {
        detailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      })
    } catch (error) {
      setNotice(error.message)
    } finally {
      setAssisting(false)
      setAssistingProjectId('')
    }
  }

  async function addProject(event) {
    event.preventDefault()
    try {
      const created = await api.createAirdropProject(newProject)
      setNotice(`已加入空投项目：${created.name}`)
      setSelectedId(created.id)
      setNewProject({ ...newProject, name: '', chain: '', official_url: '', notes: '' })
      await refresh()
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function updateTask(task, patch = {}) {
    if (!selected) return
    try {
      const payload = {
        status: patch.status || task.status || taskForm.status,
        evidence: patch.evidence ?? task.evidence ?? '',
        tx_hash: patch.tx_hash ?? task.tx_hash ?? '',
        cost_usd: patch.cost_usd ?? task.cost_usd ?? 0
      }
      await api.updateAirdropTask(selected.id, task.id, payload)
      setNotice(`任务已更新：${task.title}`)
      await refresh()
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function saveTask(event) {
    event.preventDefault()
    const task = selected?.tasks?.find((item) => item.id === taskForm.task_id)
    if (!selected || !task) return
    try {
      await api.updateAirdropTask(selected.id, task.id, {
        status: taskForm.status,
        evidence: taskForm.evidence,
        tx_hash: taskForm.tx_hash,
        cost_usd: Number(taskForm.cost_usd || 0)
      })
      setNotice(`证据已保存：${task.title}`)
      await refresh()
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function addWallet(event) {
    event.preventDefault()
    try {
      await api.upsertAirdropWallet({
        ...walletForm,
        chains: walletForm.chains.split(',').map((item) => item.trim()).filter(Boolean)
      })
      setNotice(`钱包标签已保存：${walletForm.label}`)
      setWalletForm({ ...walletForm, label: '', notes: '' })
      await refresh()
    } catch (error) {
      setNotice(error.message)
    }
  }

  function focusProject(project) {
    setSelectedId(project.id)
    setAssistantPlan(null)
    setNotice(`已打开 ${project.name} 的详情`)
    window.requestAnimationFrame(() => {
      detailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
  }

  return (
    <div className="page-stack">
      <section className="metric-grid four">
        <MetricCard label="项目数" value={metrics.project_count || 0} helper={`${metrics.active_count || 0} 个进行中 / ${metrics.high_priority_count || 0} 个高优先`} tone="good" />
        <MetricCard label="已检查" value={`${metrics.checked_count || 0}/${metrics.project_count || 0}`} helper="官方源状态" tone={(metrics.checked_count || 0) ? 'good' : 'warn'} />
        <MetricCard label="总成本" value={money(metrics.total_cost_usd || 0)} helper="gas / fee / 工具费" tone={(metrics.total_cost_usd || 0) > 0 ? 'warn' : 'neutral'} />
        <MetricCard label="上次刷新" value={uiText(airdrops?.last_refresh_at ? 'online' : 'pending')} helper={dateText(airdrops?.last_refresh_at)} tone={airdrops?.last_refresh_at ? 'good' : 'warn'} />
      </section>

      <div className="airdrop-layout">
        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>实时源</h2>
              <p>官方页面、文档和任务页的在线检查结果。</p>
            </div>
            <StatusPill value={uiText(refreshing ? 'refreshing' : 'manual')} tone={refreshing ? 'warn' : 'good'} />
          </div>
          <div className="inline-actions live-actions">
            <button className="primary-button" type="button" onClick={() => refreshSources()} disabled={refreshing}>
              <RefreshCw size={17} />
              <span>刷新全部</span>
            </button>
            <button className="secondary-button" type="button" onClick={() => selected && refreshSources(selected.id)} disabled={refreshing || !selected}>
              <RefreshCw size={17} />
              <span>刷新选中</span>
            </button>
          </div>
          <div className="source-list">
            {projects.slice(0, 6).map((project) => (
              <button key={project.id} type="button" className={selected?.id === project.id ? 'active' : ''} onClick={() => {
                setSelectedId(project.id)
                setAssistantPlan(null)
              }}>
                <span>{project.name}</span>
                <StatusPill value={uiText(project.source_health || 'not_checked')} tone={statusTone(project.source_health)} />
              </button>
            ))}
          </div>
          <div className="warning-strip">
            平台只记录项目和证据；签名、授权、转账仍在钱包里手动确认，主钱包不要授权陌生合约。
          </div>

          <form className="form-stack" onSubmit={addProject}>
            <div className="panel-head compact-head">
              <h2>新增项目</h2>
              <Plus size={17} />
            </div>
            <label>名称<input value={newProject.name} onChange={(event) => setNewProject({ ...newProject, name: event.target.value })} placeholder="项目名" required /></label>
            <label>链<input value={newProject.chain} onChange={(event) => setNewProject({ ...newProject, chain: event.target.value })} placeholder="EVM / Solana / Testnet" /></label>
            <label>官方入口<input value={newProject.official_url} onChange={(event) => setNewProject({ ...newProject, official_url: event.target.value })} placeholder="https://..." required /></label>
            <div className="mini-form-grid">
              <label>优先级<select value={newProject.priority} onChange={(event) => setNewProject({ ...newProject, priority: event.target.value })}><option value="high">high</option><option value="medium">medium</option><option value="low">low</option></select></label>
              <label>风险<select value={newProject.risk_level} onChange={(event) => setNewProject({ ...newProject, risk_level: event.target.value })}><option value="low">low</option><option value="medium">medium</option><option value="high">high</option></select></label>
            </div>
            <label>备注<textarea rows="3" value={newProject.notes} onChange={(event) => setNewProject({ ...newProject, notes: event.target.value })} /></label>
            <button className="secondary-button full" type="submit">
              <Plus size={17} />
              <span>加入项目库</span>
            </button>
          </form>
        </section>

        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>项目看板</h2>
              <p>{projects.length} 个项目；按优先级、风险和任务进度推进。</p>
            </div>
            <StatusPill value={uiText('official-source first')} tone="good" />
          </div>
          <div className="airdrop-project-grid">
            {projects.map((project) => (
              <article key={project.id} className={selected?.id === project.id ? 'airdrop-card active' : 'airdrop-card'} onClick={() => focusProject(project)}>
                <div className="panel-head">
                  <div>
                    <h3>{project.name}</h3>
                    <p>{project.chain} / {categoryText(project.category)}</p>
                  </div>
                  <StatusPill value={uiText(project.status)} tone={statusTone(project.status)} />
                </div>
                <div className="airdrop-tags">
                  <span>{uiText(project.priority)}</span>
                  <span>{airdropStageText(project.stage)}</span>
                  <span>{riskLabel(project.risk_level)}</span>
                  <span>{costLabel(project.cost_level)}</span>
                </div>
                <p>{project.notes}</p>
                <div className="task-progress">
                  <span style={{ width: `${project.summary?.task_total ? Math.round((project.summary.task_done / project.summary.task_total) * 100) : 0}%` }} />
                </div>
                <div className="airdrop-card-foot">
                  <span>{project.summary?.task_done || 0}/{project.summary?.task_total || 0} 个任务</span>
                  <span>{money(project.summary?.total_cost_usd || 0)}</span>
                </div>
                <div className="inline-actions airdrop-card-actions">
                  <button className="primary-button small" type="button" onClick={(event) => {
                    event.stopPropagation()
                    runAssist(project)
                  }} disabled={assisting}>
                    <PlugZap size={15} />
                    <span>{assisting && assistingProjectId === project.id ? '处理中...' : '帮我处理'}</span>
                  </button>
                  <button className="secondary-button small" type="button" onClick={(event) => {
                    event.stopPropagation()
                    focusProject(project)
                  }}>
                    <ListChecks size={15} />
                    <span>定位详情</span>
                  </button>
                  {project.official_url ? (
                    <a
                      className="primary-button small"
                      href={project.official_url}
                      target="_blank"
                      rel="noreferrer"
                      onClick={(event) => event.stopPropagation()}
                    >
                      <ExternalLink size={15} />
                      <span>打开官网</span>
                    </a>
                  ) : null}
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="panel airdrop-detail" ref={detailRef}>
          <div className="panel-head">
            <div>
              <h2>{selected?.name || '项目详情'}</h2>
              <p>{selected?.official_url}</p>
            </div>
            {selected?.official_url ? (
              <a className="secondary-button small" href={selected.official_url} target="_blank" rel="noreferrer">
                <ExternalLink size={15} />
                <span>官方</span>
              </a>
            ) : null}
          </div>

          <div className="compact-grid">
            <MetricCard label="源状态" value={uiText(selected?.source_health || 'not_checked')} helper={dateText(selected?.last_checked_at)} tone={statusTone(selected?.source_health)} />
            <MetricCard label="信号" value={selected?.signals?.length || 0} helper={(selected?.signals || []).join(', ') || '等待刷新'} tone={(selected?.signals?.length || 0) ? 'good' : 'neutral'} />
          </div>

          <section className="assistant-panel">
            <div className="panel-head">
              <div>
                <h3>半自动引导</h3>
                <p>我先替你刷新官网、判断状态、拆步骤；需要钱包签名和发交易时再交给你。</p>
              </div>
              <div className="inline-actions">
                <StatusPill value={uiText(assistantPlan?.status || 'manual')} tone={statusTone(assistantPlan?.status)} />
                <button className="primary-button small" type="button" onClick={() => runAssist(selected)} disabled={!selected || assisting}>
                  <PlugZap size={15} />
                  <span>{assisting ? '处理中...' : '帮我处理'}</span>
                </button>
              </div>
            </div>

            {assistantPlan ? (
              <div className="assistant-plan-grid">
                <article className="assistant-summary-card">
                  <strong>{assistantPlan.headline}</strong>
                  <p>{assistantPlan.summary}</p>
                  {assistantPlan.primary_action?.url ? (
                    <a className="primary-button small" href={assistantPlan.primary_action.url} target="_blank" rel="noreferrer">
                      <ExternalLink size={15} />
                      <span>{assistantPlan.primary_action.label || '打开官网'}</span>
                    </a>
                  ) : null}
                </article>

                <article className="assistant-checklist">
                  <h4>我已经帮你做了什么</h4>
                  <ul>
                    {(assistantPlan.auto_done || []).map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </article>

                <article className="assistant-checklist">
                  <h4>现在你自己做什么</h4>
                  <ol>
                    {(assistantPlan.manual_steps || []).map((item) => <li key={item}>{item}</li>)}
                  </ol>
                </article>

                <article className="assistant-checklist">
                  <h4>下一步确认点</h4>
                  <ul>
                    {(assistantPlan.next_checkpoints || []).map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </article>

                <article className="assistant-checklist danger">
                  <h4>不要做</h4>
                  <ul>
                    {(assistantPlan.do_not_do || []).map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </article>
              </div>
            ) : (
              <div className="assistant-empty">
                <strong>点一下“帮我处理”</strong>
                <span>我会先刷新这个项目的官方入口，然后直接告诉你这项目现在还能不能做、你应该点哪里、哪些必须你亲手确认。</span>
              </div>
            )}
          </section>

          <div className="source-result-grid">
            {(selected?.source_results || []).map((source) => (
              <article key={source.url}>
                <div className="panel-head">
                  <strong>{source.label}</strong>
                  <StatusPill value={uiText(source.ok ? 'online' : 'error')} tone={source.ok ? 'good' : 'danger'} />
                </div>
                <span>{source.title || source.error || source.url}</span>
                <small>{source.signals?.join(', ') || '无信号'} / {source.status_code || '-'}</small>
              </article>
            ))}
            {!selected?.source_results?.length ? <p className="muted">还没有实时检查结果。</p> : null}
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>任务</th>
                  <th>类型</th>
                  <th>成本</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {(selected?.tasks || []).map((task) => (
                  <tr key={task.id}>
                    <td>
                      <strong>{task.title}</strong>
                      <span className="table-note">{task.evidence || task.tx_hash || '-'}</span>
                    </td>
                    <td>{taskKindText(task.kind)}</td>
                    <td>{money(task.cost_usd || 0)}</td>
                    <td><StatusPill value={uiText(task.status)} tone={statusTone(task.status)} /></td>
                    <td>
                      <div className="inline-actions">
                        <button className="secondary-button small" type="button" onClick={() => {
                          setTaskForm({ task_id: task.id, status: task.status, evidence: task.evidence || '', tx_hash: task.tx_hash || '', cost_usd: task.cost_usd || 0 })
                        }}>
                          <ListChecks size={15} />
                          <span>编辑</span>
                        </button>
                        <button className="primary-button small" type="button" onClick={() => updateTask(task, { status: 'done' })}>
                          <CheckCircle2 size={15} />
                          <span>完成</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <form className="evidence-grid" onSubmit={saveTask}>
            <label>任务<select value={taskForm.task_id} onChange={(event) => setTaskForm({ ...taskForm, task_id: event.target.value })}>{(selected?.tasks || []).map((task) => <option key={task.id} value={task.id}>{shortText(task.title, 34)}</option>)}</select></label>
            <label>状态<select value={taskForm.status} onChange={(event) => setTaskForm({ ...taskForm, status: event.target.value })}><option value="todo">待做</option><option value="done">完成</option><option value="blocked">阻塞</option></select></label>
            <label>成本 USD<input type="number" min="0" step="0.0001" value={taskForm.cost_usd} onChange={(event) => setTaskForm({ ...taskForm, cost_usd: event.target.value })} /></label>
            <label>Tx / 证据<input value={taskForm.tx_hash} onChange={(event) => setTaskForm({ ...taskForm, tx_hash: event.target.value })} placeholder="tx hash 或链接" /></label>
            <label className="wide-field">备注<textarea rows="3" value={taskForm.evidence} onChange={(event) => setTaskForm({ ...taskForm, evidence: event.target.value })} /></label>
            <button className="primary-button" type="submit">保存证据</button>
          </form>
        </section>

        <section className="panel">
          <div className="panel-head">
            <h2>钱包标签</h2>
            <StatusPill value={`${wallets.length} 个`} tone="neutral" />
          </div>
          <div className="wallet-list">
            {wallets.map((wallet) => (
              <article key={wallet.id}>
                <WalletCards size={17} />
                <div>
                  <strong>{wallet.label}</strong>
                  <span>{wallet.chains?.join(', ')} / {wallet.role}</span>
                  <small>{wallet.notes}</small>
                </div>
                <StatusPill value={uiText(wallet.status)} tone={statusTone(wallet.status)} />
              </article>
            ))}
          </div>
          <form className="form-stack" onSubmit={addWallet}>
            <label>标签<input value={walletForm.label} onChange={(event) => setWalletForm({ ...walletForm, label: event.target.value })} placeholder="比如 小额 EVM 1" required /></label>
            <label>链<input value={walletForm.chains} onChange={(event) => setWalletForm({ ...walletForm, chains: event.target.value })} /></label>
            <label>用途<input value={walletForm.role} onChange={(event) => setWalletForm({ ...walletForm, role: event.target.value })} /></label>
            <label>备注<textarea rows="3" value={walletForm.notes} onChange={(event) => setWalletForm({ ...walletForm, notes: event.target.value })} /></label>
            <button className="secondary-button full" type="submit">保存钱包标签</button>
          </form>
        </section>

        <section className="panel">
          <div className="panel-head">
            <h2>空投日志</h2>
            <ShieldAlert size={18} />
          </div>
          <div className="activity-list">
            {activityLog.map((item) => (
              <article key={item.id}>
                <StatusPill value={uiText(item.severity)} tone={statusTone(item.severity)} />
                <div>
                  <strong>{item.title}</strong>
                  <span>{item.body}</span>
                  <small>{dateText(item.created_at)}</small>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

function TemplatesPage({ templates, setNotice, refresh }) {
  async function clone(template) {
    try {
      const created = await api.cloneTemplate(template.id)
      setNotice(`已从模板生成策略草稿：${created.name}`)
      await refresh()
    } catch (error) {
      setNotice(error.message)
    }
  }

  return (
    <div className="page-stack">
      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>Bot 模板中心</h2>
            <p>参考成熟平台的 Grid、DCA、Signal Bot，但这里只生成 dry-run 策略草稿。</p>
          </div>
          <StatusPill value={uiText('dry-run templates')} tone="good" />
        </div>
        <div className="template-grid">
          {templates.map((template) => (
            <article className="template-card" key={template.id}>
              <div className="panel-head">
                <div>
                  <h3>{template.name}</h3>
                  <p>{template.exchange} / {template.timeframe}</p>
                </div>
                <StatusPill value={uiText(template.type)} tone="neutral" />
              </div>
              <div className="template-settings">
                {Object.entries(template.settings || {}).map(([key, value]) => (
                  <div key={key}>
                    <span>{key}</span>
                    <strong>{String(value)}</strong>
                  </div>
                ))}
              </div>
              <div className="risk-tags">
                {template.risk?.map((item) => <span key={item}>{item}</span>)}
              </div>
              <button className="primary-button full" onClick={() => clone(template)}>生成策略草稿</button>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}

function SignalsPage({ signals, alerts }) {
  return (
    <div className="page-grid">
      <section className="panel">
        <div className="panel-head">
          <h2>信号中心</h2>
          <StatusPill value={uiText('advisory only')} tone="good" />
        </div>
        <div className="signal-list">
          {signals.map((signal) => (
            <article key={signal.id}>
              <div className="panel-head">
                <div>
                  <h3>{signal.pair}</h3>
                  <p>{signal.source}</p>
                </div>
                <StatusPill value={uiText(signal.direction)} tone={signal.direction === 'pause' ? 'danger' : 'neutral'} />
              </div>
              <strong>{signal.message}</strong>
              <span>{signal.evidence}</span>
              <small>{signal.action}</small>
              <div className="confidence"><span style={{ width: `${Math.round(signal.confidence * 100)}%` }} /></div>
            </article>
          ))}
        </div>
      </section>
      <section className="panel">
        <div className="panel-head">
          <h2>告警</h2>
          <StatusPill value={`${alerts.length} 条进行中`} tone={alerts.length ? 'warn' : 'good'} />
        </div>
        <div className="alert-list">
          {alerts.map((alert) => (
            <article key={alert.id}>
              <StatusPill value={uiText(alert.severity)} tone={alert.severity === 'high' ? 'danger' : 'warn'} />
              <div>
                <strong>{alert.title}</strong>
                <span>{alert.detail}</span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}

function BotsPage({ bots, setNotice, refresh }) {
  const [logBot, setLogBot] = useState('okx_spot_dryrun')
  const [logs, setLogs] = useState('')

  async function action(bot, value) {
    try {
      const task = await api.botAction(bot.id, value)
      setNotice(`任务已进入队列：${actionLabels[value] || value} (${task.id.slice(0, 8)})`)
      await refresh()
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function loadLogs(botId) {
    setLogBot(botId)
    try {
      const payload = await api.botLogs(botId)
      setLogs(payload.output || payload.error || '暂无日志')
    } catch (error) {
      setLogs(error.message)
    }
  }

  return (
    <div className="page-stack">
      <div className="bot-grid">
        {bots.map((bot) => (
          <section className="panel bot-card" key={bot.id}>
            <div className="panel-head">
              <div>
                <h2>{bot.name}</h2>
                <p>{bot.warning || '本地主要 Dry-run 路线。'}</p>
              </div>
              <StatusPill value={uiText(bot.runtime?.state || 'unknown')} tone={bot.runtime?.state === 'running' ? 'good' : 'neutral'} />
            </div>
            <div className="compact-grid">
              <MetricCard label="WebUI" value={uiText(bot.api?.reachable ? 'online' : 'offline')} helper={bot.api?.url} tone={bot.api?.reachable ? 'good' : 'neutral'} />
              <MetricCard label="持仓中" value={bot.trades?.open_trades || 0} helper={`已平仓 ${bot.trades?.closed_trades || 0} 笔`} />
            </div>
            <div className="check-list">
              {bot.safety?.checks?.map((check) => (
                <div key={check.code}>
                  <StatusPill value={check.passed ? '通过' : '失败'} tone={check.passed ? 'good' : 'danger'} />
                  <span>{check.message}</span>
                </div>
              ))}
            </div>
            <div className="inline-actions">
              {bot.actions.map((item) => (
                <button key={item} className={item === 'stop' ? 'danger-button small' : 'secondary-button small'} onClick={() => action(bot, item)}>
                  {item === 'stop' ? <Square size={15} /> : item.includes('dryrun') ? <Play size={15} /> : <History size={15} />}
                  <span>{actionLabels[item] || item}</span>
                </button>
              ))}
              <button className="secondary-button small" onClick={() => loadLogs(bot.id)}>
                <FileText size={15} />
                <span>日志</span>
              </button>
            </div>
          </section>
        ))}
      </div>
      <section className="panel">
        <div className="panel-head">
          <h2>容器日志</h2>
          <StatusPill value={logBot} tone="neutral" />
        </div>
        <pre className="log-box">{logs || '点击 Bot 卡片中的日志按钮查看。'}</pre>
      </section>
    </div>
  )
}

function StrategyPage({ strategies, setStrategies, setNotice }) {
  const [form, setForm] = useState({
    name: '',
    timeframe: '15m',
    pairs: 'BTC/USDT,ETH/USDT',
    entry_rules: '1h EMA50 rising\n15m RSI below 60\nVolume above 30-candle mean',
    exit_rules: 'Close below EMA50\nStoploss -5%\nPause after 3 losses',
    risk_notes: 'Draft only; requires backtest before dry-run.'
  })

  async function submit(event) {
    event.preventDefault()
    try {
      const payload = {
        name: form.name,
        timeframe: form.timeframe,
        pairs: form.pairs.split(',').map((item) => item.trim()).filter(Boolean),
        entry_rules: form.entry_rules.split('\n').map((item) => item.trim()).filter(Boolean),
        exit_rules: form.exit_rules.split('\n').map((item) => item.trim()).filter(Boolean),
        risk_notes: form.risk_notes
      }
      const created = await api.createStrategy(payload)
      setStrategies([created, ...strategies])
      setNotice(`策略草稿已保存：${created.name}`)
      setForm({ ...form, name: '' })
    } catch (error) {
      setNotice(error.message)
    }
  }

  return (
    <div className="page-grid">
      <section className="panel">
        <div className="panel-head">
          <h2>规则生成器</h2>
          <StatusPill value="免代码草稿" tone="good" />
        </div>
        <form className="form-stack" onSubmit={submit}>
          <label>
            名称
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="比如 趋势回踩 v2 / Trend Pullback v2" required />
          </label>
          <label>
            周期
            <select value={form.timeframe} onChange={(event) => setForm({ ...form, timeframe: event.target.value })}>
              <option>15m</option>
              <option>15m + 1h filter</option>
              <option>1h</option>
            </select>
          </label>
          <label>
            交易对
            <input value={form.pairs} onChange={(event) => setForm({ ...form, pairs: event.target.value })} />
          </label>
          <label>
            入场规则
            <textarea rows="5" value={form.entry_rules} onChange={(event) => setForm({ ...form, entry_rules: event.target.value })} />
          </label>
          <label>
            出场规则
            <textarea rows="4" value={form.exit_rules} onChange={(event) => setForm({ ...form, exit_rules: event.target.value })} />
          </label>
          <label>
            风险备注
            <textarea rows="3" value={form.risk_notes} onChange={(event) => setForm({ ...form, risk_notes: event.target.value })} />
          </label>
          <button className="primary-button full" type="submit">保存草稿</button>
        </form>
      </section>
      <section className="panel">
        <div className="panel-head">
          <h2>策略库</h2>
          <span>{strategies.length} 个版本</span>
        </div>
        <div className="strategy-list">
          {strategies.map((strategy) => (
            <article key={strategy.id} className="strategy-item">
              <div className="panel-head">
                <div>
                  <h3>{strategy.name}</h3>
                  <p>{strategy.timeframe} / {strategy.pairs?.join(', ')}</p>
                </div>
                <StatusPill value={uiText(strategy.status)} tone={strategy.status === 'active' ? 'good' : 'neutral'} />
              </div>
              <div className="rule-columns">
                <div>
                  <strong>入场</strong>
                  {strategy.entry_rules?.map((rule) => <span key={rule}>{rule}</span>)}
                </div>
                <div>
                  <strong>出场</strong>
                  {strategy.exit_rules?.map((rule) => <span key={rule}>{rule}</span>)}
                </div>
              </div>
              <p className="muted">{strategy.risk_notes}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}

function BacktestsPage({ backtests, setNotice, refresh }) {
  async function run(exchange) {
    try {
      const task = await api.runBacktest(exchange)
      setNotice(`${exchange.toUpperCase()} 回测已进入队列：${task.id.slice(0, 8)}`)
      await refresh()
    } catch (error) {
      setNotice(error.message)
    }
  }

  return (
    <div className="page-stack">
      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>回测中心</h2>
            <p>读取 Freqtrade 回测产物，重点看收益、回撤、连续亏损。</p>
          </div>
          <div className="inline-actions">
            <button className="primary-button" onClick={() => run('okx')}>
              <TestTube2 size={18} />
              <span>跑 OKX 回测</span>
            </button>
            <button className="secondary-button" onClick={() => run('binance')}>
              <TestTube2 size={18} />
              <span>跑 Binance 回测</span>
            </button>
          </div>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>交易所</th>
                <th>策略</th>
                <th>周期</th>
                <th>交易数</th>
                <th>收益</th>
                <th>胜率</th>
                <th>回撤</th>
                <th>连续亏损</th>
              </tr>
            </thead>
            <tbody>
              {backtests.map((item) => (
                <tr key={item.id}>
                  <td>{item.exchange}</td>
                  <td>{item.strategy}</td>
                  <td>{item.timeframe}</td>
                  <td>{item.total_trades}</td>
                  <td className={item.profit_abs >= 0 ? 'positive' : 'negative'}>{money(item.profit_abs)}</td>
                  <td>{pct(item.winrate_pct)}</td>
                  <td>{pct(item.max_drawdown_pct)}</td>
                  <td>{item.max_consecutive_losses}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

function RiskPage({ overview, refresh, setNotice }) {
  const risk = overview?.risk
  const [form, setForm] = useState(null)

  useEffect(() => {
    if (risk) setForm({ ...risk, allowed_pairs: risk.allowed_pairs?.join(',') || '' })
  }, [risk])

  async function save(event) {
    event.preventDefault()
    try {
      const payload = {
        ...form,
        max_open_trades: Number(form.max_open_trades),
        stake_amount: Number(form.stake_amount),
        daily_loss_limit_pct: Number(form.daily_loss_limit_pct),
        pause_drawdown_pct: Number(form.pause_drawdown_pct),
        hard_stop_drawdown_pct: Number(form.hard_stop_drawdown_pct),
        max_consecutive_losses: Number(form.max_consecutive_losses),
        allowed_pairs: form.allowed_pairs.split(',').map((item) => item.trim()).filter(Boolean)
      }
      await api.updateRisk(payload)
      setNotice('风控阈值已保存')
      await refresh()
    } catch (error) {
      setNotice(error.message)
    }
  }

  if (!form) return <div className="panel">加载中</div>

  return (
    <div className="page-grid">
      <section className="panel">
        <div className="panel-head">
          <h2>风控阈值</h2>
          <StatusPill value={uiText('hard capped')} tone="good" />
        </div>
        <form className="form-stack" onSubmit={save}>
          <label>最大持仓数<input type="number" value={form.max_open_trades} onChange={(event) => setForm({ ...form, max_open_trades: event.target.value })} /></label>
          <label>单笔金额<input type="number" value={form.stake_amount} onChange={(event) => setForm({ ...form, stake_amount: event.target.value })} /></label>
          <label>日内亏损暂停 %<input type="number" value={form.daily_loss_limit_pct} onChange={(event) => setForm({ ...form, daily_loss_limit_pct: event.target.value })} /></label>
          <label>总回撤暂停 %<input type="number" value={form.pause_drawdown_pct} onChange={(event) => setForm({ ...form, pause_drawdown_pct: event.target.value })} /></label>
          <label>总回撤停止 %<input type="number" value={form.hard_stop_drawdown_pct} onChange={(event) => setForm({ ...form, hard_stop_drawdown_pct: event.target.value })} /></label>
          <label>连续亏损上限<input type="number" value={form.max_consecutive_losses} onChange={(event) => setForm({ ...form, max_consecutive_losses: event.target.value })} /></label>
          <label>允许交易对<input value={form.allowed_pairs} onChange={(event) => setForm({ ...form, allowed_pairs: event.target.value })} /></label>
          <button className="primary-button full" type="submit">保存</button>
        </form>
      </section>
      <section className="panel">
        <div className="panel-head">
          <h2>禁止事项</h2>
          <StatusPill value={uiText('locked')} tone="danger" />
        </div>
        <div className="forbidden-grid">
          {risk?.forbidden?.map((item) => (
            <div key={item}>
              <LockKeyhole size={17} />
              <span>{item}</span>
            </div>
          ))}
        </div>
        <div className="warning-strip">
          后端接口会拒绝 live、withdraw、futures、margin、short、leverage 相关动作。
        </div>
      </section>
    </div>
  )
}

function MarketPage({ overview }) {
  return (
    <div className="page-stack">
      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>市场观察</h2>
            <p>当前以 OKX 三个高流动性现货交易对作为 dry-run 宇宙。</p>
          </div>
          <StatusPill value="OKX" tone="good" />
        </div>
        <div className="market-grid">
          {(overview?.watchlist || []).map((item) => (
            <article key={item.pair} className="market-card">
              <div className="panel-head">
                <h3>{item.pair}</h3>
                <StatusPill value={uiText(item.enabled ? 'enabled' : 'off')} tone={item.enabled ? 'good' : 'neutral'} />
              </div>
              <span>{item.exchange}</span>
              <strong>{item.role}</strong>
              <Sparkline values={item.pair.startsWith('SOL') ? [10, 9, 11, 8, 12, 13, 12] : [12, 13, 11, 15, 16, 15, 18]} />
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}

function LogsPage({ tasks }) {
  return (
    <div className="page-stack">
      <TaskStrip tasks={tasks} full />
      <section className="panel">
        <div className="panel-head">
          <h2>最近任务输出</h2>
          <StatusPill value={uiText('tail')} tone="neutral" />
        </div>
        <div className="task-output-list">
          {tasks.map((task) => (
            <article key={task.id}>
              <div className="panel-head">
                <strong>{task.action}</strong>
                <StatusPill value={uiText(task.status)} tone={task.status === 'success' ? 'good' : task.status === 'failed' ? 'danger' : 'neutral'} />
              </div>
              <pre className="log-box compact">{task.output_tail || '暂无输出'}</pre>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}

function SettingsPage({ settings, overview }) {
  return (
    <div className="page-grid">
      <section className="panel">
        <div className="panel-head">
          <h2>路径</h2>
          <StatusPill value={uiText('local')} tone="good" />
        </div>
        <dl className="kv-list">
          <dt>Freqtrade</dt>
          <dd>{settings?.freqtrade_dir}</dd>
          <dt>状态文件</dt>
          <dd>{settings?.state_path}</dd>
          <dt>API</dt>
          <dd>http://127.0.0.1:8011/api</dd>
          <dt>前端</dt>
          <dd>http://127.0.0.1:5175</dd>
        </dl>
      </section>
      <section className="panel">
        <div className="panel-head">
          <h2>配置摘要</h2>
          <StatusPill value={uiText(overview?.profile?.mode || 'dry-run only')} tone="good" />
        </div>
        <dl className="kv-list">
          <dt>用户</dt>
          <dd>{overview?.profile?.owner}</dd>
          <dt>钱包</dt>
          <dd>{money(overview?.profile?.paper_wallet || 0)}</dd>
          <dt>目标</dt>
          <dd>{overview?.profile?.product_target}</dd>
        </dl>
      </section>
    </div>
  )
}

function TaskStrip({ tasks = [], full = false }) {
  return (
    <section className={`panel ${full ? '' : 'wide'}`}>
      <div className="panel-head">
        <h2>任务队列</h2>
        <span>{tasks.length} 条</span>
      </div>
      <div className="task-strip">
        {tasks.length ? tasks.slice(0, full ? 80 : 8).map((task) => (
          <div key={task.id}>
            <StatusPill value={uiText(task.status)} tone={task.status === 'success' ? 'good' : task.status === 'failed' ? 'danger' : 'neutral'} />
            <span>{task.action}</span>
            <small>{shortText(task.output_tail || task.created_at, 120)}</small>
          </div>
        )) : <p className="muted">暂无后台任务。</p>}
      </div>
    </section>
  )
}
