export function pct(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  return `${Number(value).toFixed(digits)}%`
}

export function money(value, currency = 'USDT') {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  return `${Number(value).toFixed(2)} ${currency}`
}

export function shortText(value, limit = 96) {
  if (!value) return ''
  return value.length > limit ? `${value.slice(0, limit)}...` : value
}
