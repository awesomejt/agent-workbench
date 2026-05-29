const COLORS = {
  discovery: 'bg-slate-100 text-slate-600',
  design: 'bg-blue-100 text-blue-700',
  implementation: 'bg-indigo-100 text-indigo-700',
  testing: 'bg-orange-100 text-orange-700',
  review: 'bg-green-100 text-green-700',
}

export default function PhaseBadge({ phase }) {
  if (!phase) return null
  const cls = COLORS[phase] ?? 'bg-slate-100 text-slate-600'
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-medium uppercase tracking-wide ${cls}`}
    >
      {phase}
    </span>
  )
}
