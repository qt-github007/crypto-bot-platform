export default function StatusPill({ value, tone = 'neutral' }) {
  return <span className={`status-pill ${tone}`}>{value}</span>
}
