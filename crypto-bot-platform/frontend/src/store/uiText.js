const UI_TEXT_MAP = {
  unknown: '未知',
  running: '运行中',
  stopped: '已停止',
  unavailable: '不可用',
  online: '在线',
  offline: '离线',
  passed: '通过',
  review: '需复核',
  locked: '锁定',
  'single user': '单用户',
  preflight_required: '需预检',
  not_connected: '未连接',
  connected: '已连接',
  blocked: '已拦截',
  'local env': '本地环境',
  'not saved': '未保存',
  check: '检查',
  ok: '正常',
  no: '未通过',
  manual: '手动',
  refreshing: '刷新中',
  active: '进行中',
  watch: '观察',
  ended: '已结束',
  advanced: '进阶',
  manual_only: '仅手动',
  partial: '部分成功',
  error: '错误',
  ready: '就绪',
  not_checked: '未检查',
  offline: '离线',
  queued: '排队中',
  success: '成功',
  failed: '失败',
  pending: '待处理',
  completed: '已完成',
  draft: '草稿',
  template: '模板',
  grid: '网格',
  dca: 'DCA',
  signal: '信号',
  pause: '暂停',
  buy: '买入',
  sell: '卖出',
  limit: '限价',
  market: '市价',
  high: '高',
  medium: '中',
  low: '低',
  'official-source first': '官方源优先',
  'dry-run templates': 'Dry-run 模板',
  'advisory only': '仅供参考',
  'live order terminal': '实盘下单终端',
  'read / cancel': '读取 / 撤单',
  'real exchange api': '真实交易所 API',
  'hard capped': '硬限制',
  enabled: '已启用',
  off: '关闭',
  tail: '尾部输出',
  local: '本地',
  'dry-run only': '仅 Dry-run',
  open: '未成交',
  new: '新建',
  submitted: '已提交',
  live: '生效中',
  filled: '已成交',
  closed: '已关闭',
  canceled: '已撤销',
  cancelled: '已撤销',
  rejected: '已拒绝',
  expired: '已过期',
}

const TASK_KIND_MAP = {
  research: '研究',
  interaction: '交互',
  review: '复盘',
  safety: '安全',
  risk: '风险',
  evidence: '证据',
  monitor: '观察',
}

const AIRDROP_STAGE_MAP = {
  rewards: '奖励',
  points: '积分',
  quests: '任务',
  quest: '任务',
  monitor: '观察',
}

const CATEGORY_MAP = {
  Rewards: '奖励',
  Reward: '奖励',
  Quests: '任务',
  Quest: '任务',
  Wallet: '钱包',
  Points: '积分',
  Ecosystem: '生态',
  'Future season': '未来赛季',
  Testnet: '测试网',
  'Perp DEX': '永续 DEX',
}

export function uiText(value) {
  if (value === null || value === undefined) return ''
  const text = String(value)
  const normalized = text.toLowerCase()
  return UI_TEXT_MAP[normalized] || text
}

export function taskKindText(value) {
  if (!value) return ''
  return TASK_KIND_MAP[String(value).toLowerCase()] || value
}

export function airdropStageText(value) {
  if (!value) return ''
  return AIRDROP_STAGE_MAP[String(value).toLowerCase()] || value
}

export function categoryText(value) {
  if (!value) return ''
  let result = String(value)
  for (const [source, target] of Object.entries(CATEGORY_MAP)) {
    result = result.replaceAll(source, target)
  }
  return result
}

export function riskLabel(level) {
  return level ? `${uiText(level)}风险` : ''
}

export function costLabel(level) {
  return level ? `${uiText(level)}成本` : ''
}
