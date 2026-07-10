const API_BASE = import.meta.env.VITE_API_BASE || '/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `HTTP ${response.status}`)
  }
  return response.json()
}

export const api = {
  overview: () => request('/overview'),
  settings: () => request('/settings'),
  bots: () => request('/bots'),
  bot: (id) => request(`/bots/${id}`),
  botLogs: (id) => request(`/bots/${id}/logs?lines=260`),
  botAction: (id, action) => request(`/bots/${id}/actions`, { method: 'POST', body: JSON.stringify({ action }) }),
  tasks: () => request('/tasks'),
  backtests: () => request('/backtests'),
  runBacktest: (exchange = 'okx') => request(`/backtests/run?exchange=${encodeURIComponent(exchange)}`, { method: 'POST' }),
  portfolio: () => request('/portfolio'),
  signals: () => request('/signals'),
  alerts: () => request('/alerts'),
  templates: () => request('/templates'),
  cloneTemplate: (id) => request(`/templates/${id}/clone`, { method: 'POST' }),
  liveStatus: () => request('/live/status'),
  connectExchange: (payload) => request('/live/accounts/connect', { method: 'POST', body: JSON.stringify(payload) }),
  refreshLiveAccount: (exchange) => request(`/live/accounts/${exchange}/refresh`, { method: 'POST' }),
  livePreflight: () => request('/live/preflight'),
  generateLiveConfig: (exchange) => request(`/live/configs/${exchange}`, { method: 'POST' }),
  startLive: (payload) => request('/live/start', { method: 'POST', body: JSON.stringify(payload) }),
  previewLiveOrder: (payload) => request('/live/orders/preview', { method: 'POST', body: JSON.stringify(payload) }),
  submitLiveOrder: (payload) => request('/live/orders', { method: 'POST', body: JSON.stringify(payload) }),
  liveOpenOrders: (exchange, pair) => request(`/live/orders/open?exchange=${encodeURIComponent(exchange)}&pair=${encodeURIComponent(pair)}`),
  liveOrderHistory: (exchange, pair) => request(`/live/orders/history?exchange=${encodeURIComponent(exchange)}&pair=${encodeURIComponent(pair)}`),
  cancelLiveOrder: (payload) => request('/live/orders/cancel', { method: 'POST', body: JSON.stringify(payload) }),
  liveOrders: () => request('/live/orders'),
  airdrops: () => request('/airdrops'),
  refreshAirdrops: (payload = {}) => request('/airdrops/refresh', { method: 'POST', body: JSON.stringify(payload) }),
  assistAirdrop: (projectId, payload = {}) => request(`/airdrops/${projectId}/assist`, { method: 'POST', body: JSON.stringify(payload) }),
  createAirdropProject: (payload) => request('/airdrops/projects', { method: 'POST', body: JSON.stringify(payload) }),
  updateAirdropTask: (projectId, taskId, payload) => request(`/airdrops/projects/${projectId}/tasks/${taskId}`, { method: 'PUT', body: JSON.stringify(payload) }),
  upsertAirdropWallet: (payload) => request('/airdrops/wallets', { method: 'POST', body: JSON.stringify(payload) }),
  strategies: () => request('/strategies'),
  createStrategy: (payload) => request('/strategies', { method: 'POST', body: JSON.stringify(payload) }),
  risk: () => request('/risk'),
  updateRisk: (payload) => request('/risk', { method: 'PUT', body: JSON.stringify(payload) }),
  watchlist: () => request('/market/watchlist'),
  updateWatchlist: (watchlist) => request('/market/watchlist', { method: 'PUT', body: JSON.stringify({ watchlist }) }),
  journal: () => request('/journal'),
  addJournal: (payload) => request('/journal', { method: 'POST', body: JSON.stringify(payload) })
}
