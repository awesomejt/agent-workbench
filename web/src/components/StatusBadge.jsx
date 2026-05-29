const PROJECT_COLORS = {
  active: 'bg-emerald-100 text-emerald-700',
  working: 'bg-indigo-100 text-indigo-700',
  paused: 'bg-yellow-100 text-yellow-700',
  blocked: 'bg-red-100 text-red-700',
  error: 'bg-red-200 text-red-800',
  stopped: 'bg-slate-100 text-slate-500',
}

const TASK_COLORS = {
  new: 'bg-orange-100 text-orange-700',
  pending: 'bg-slate-100 text-slate-600',
  in_progress: 'bg-indigo-100 text-indigo-700',
  blocked: 'bg-red-100 text-red-600',
  completed: 'bg-emerald-100 text-emerald-700',
  duplicate: 'bg-slate-100 text-slate-400',
  rejected: 'bg-slate-100 text-slate-400',
}

const TASK_LABELS = {
  in_progress: 'active',
}

export function ProjectStatusBadge({ status }) {
  if (!status) return null
  const cls = PROJECT_COLORS[status] ?? 'bg-slate-100 text-slate-600'
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium uppercase tracking-wide ${cls}`}>
      {status}
    </span>
  )
}

export function TaskStatusBadge({ status }) {
  if (!status) return null
  const cls = TASK_COLORS[status] ?? 'bg-slate-100 text-slate-600'
  const label = TASK_LABELS[status] ?? status
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {label}
    </span>
  )
}
