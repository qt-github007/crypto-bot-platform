export default function Sparkline({ values = [], tone = 'green' }) {
  const width = 180
  const height = 52
  const data = values.length ? values : [10, 12, 9, 16, 14, 18, 17, 21, 19]
  const min = Math.min(...data)
  const max = Math.max(...data)
  const span = max - min || 1
  const points = data
    .map((value, index) => {
      const x = (index / Math.max(data.length - 1, 1)) * width
      const y = height - ((value - min) / span) * (height - 8) - 4
      return `${x},${y}`
    })
    .join(' ')
  return (
    <svg className={`sparkline ${tone}`} viewBox={`0 0 ${width} ${height}`} role="img" aria-label="trend">
      <polyline points={points} fill="none" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
