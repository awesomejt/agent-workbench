import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchProject, fetchRuns, fetchEvents } from '../api'

const RUN_COLORS = {
  running: 'bg-indigo-100 text-indigo-700',
  completed: 'bg-emerald-100 text-emerald-700',
  failed: 'bg-red-100 text-red-600',
}

function RunStatusBadge({ status }) {
  const cls = RUN_COLORS[status] ?? 'bg-slate-100 text-slate-600'
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {status}
    </span>
  )
}

function formatDuration(startedAt, completedAt) {
  if (!completedAt) return '—'
  const ms = new Date(completedAt) - new Date(startedAt)
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${Math.round(ms / 1000)}s`
  return `${Math.round(ms / 60000)}m`
}

function RunRow({ run }) {
  const started = new Date(run.started_at)
  const dateStr = started.toLocaleDateString([], { month: 'short', day: 'numeric' })
  const timeStr = started.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

  return (
    <tr className="border-b border-slate-100 hover:bg-slate-50">
      <td className="px-4 py-2.5 text-xs text-slate-400 whitespace-nowrap">
        {dateStr} {timeStr}
      </td>
      <td className="px-4 py-2.5 text-sm font-mono text-slate-700">
        {run.agent_name}
      </td>
      <td className="px-4 py-2.5">
        <RunStatusBadge status={run.status} />
      </td>
      <td className="px-4 py-2.5 text-xs text-slate-500 font-mono">
        {run.model_id ?? '—'}
      </td>
      <td className="px-4 py-2.5 text-xs text-right text-slate-400 font-mono">
        {run.prompt_tokens != null ? run.prompt_tokens.toLocaleString() : '—'}
      </td>
      <td className="px-4 py-2.5 text-xs text-right text-slate-400 font-mono">
        {run.completion_tokens != null ? run.completion_tokens.toLocaleString() : '—'}
      </td>
      <td className="px-4 py-2.5 text-xs text-right text-slate-400 font-mono whitespace-nowrap">
        {formatDuration(run.started_at, run.completed_at)}
      </td>
      <td className="px-4 py-2.5 text-sm text-slate-600 max-w-xs truncate">
        {run.summary ?? ''}
      </td>
    </tr>
  )
}

function EventRow({ event }) {
  const ts = new Date(event.created_at)
  const timeStr = ts.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  const dateStr = ts.toLocaleDateString([], { month: 'short', day: 'numeric' })

  return (
    <tr className="border-b border-slate-100 hover:bg-slate-50">
      <td className="px-4 py-2 text-xs text-slate-400 whitespace-nowrap">
        {dateStr} {timeStr}
      </td>
      <td className="px-4 py-2 font-mono text-xs text-indigo-600">
        {event.event_type}
      </td>
      <td className="px-4 py-2 text-xs text-slate-500">
        {event.actor_name ?? '—'}
      </td>
      <td className="px-4 py-2 text-xs text-slate-400 font-mono">
        {event.task_id ? event.task_id.slice(0, 8) + '…' : '—'}
      </td>
    </tr>
  )
}

export default function ProjectRuns() {
  const { projectId } = useParams()

  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => fetchProject(projectId),
  })

  const { data: runsData, isLoading: runsLoading } = useQuery({
    queryKey: ['runs', projectId],
    queryFn: () => fetchRuns(projectId, { perPage: 50 }),
  })
  const runs = runsData?.items ?? []
  const runsTotal = runsData?.total ?? null

  const { data: events, isLoading: eventsLoading } = useQuery({
    queryKey: ['events', projectId, 'all'],
    queryFn: () => fetchEvents(projectId, { perPage: 50 }),
  })

  return (
    <div className="space-y-8">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="text-sm text-slate-500">
        <Link to="/" className="hover:text-indigo-700">Projects</Link>
        <span className="mx-2">›</span>
        <Link to={`/projects/${projectId}`} className="hover:text-indigo-700">
          {project?.name ?? projectId.slice(0, 8) + '…'}
        </Link>
        <span className="mx-2">›</span>
        <span className="text-slate-900 font-medium">Runs & Events</span>
      </nav>

      {/* Run list */}
      <section aria-labelledby="runs-heading">
        <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-200">
            <h2 id="runs-heading" className="font-semibold text-slate-900 m-0">
              Agent Runs
              {runsTotal != null && (
                <span className="ml-2 text-sm font-normal text-slate-500">
                  {runs.length < runsTotal
                    ? `${runs.length} of ${runsTotal}`
                    : runsTotal}
                </span>
              )}
            </h2>
          </div>
          {runsLoading && (
            <p className="text-slate-500 text-sm px-4 py-3">Loading…</p>
          )}
          {!runsLoading && runs.length === 0 && (
            <p className="text-slate-500 text-sm px-4 py-3">No runs yet.</p>
          )}
          {runs.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm" aria-label="Agent runs">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50">
                    <th className="px-4 py-2 text-xs font-medium text-slate-500 text-left">Started</th>
                    <th className="px-4 py-2 text-xs font-medium text-slate-500 text-left">Agent</th>
                    <th className="px-4 py-2 text-xs font-medium text-slate-500 text-left">Status</th>
                    <th className="px-4 py-2 text-xs font-medium text-slate-500 text-left">Model</th>
                    <th className="px-4 py-2 text-xs font-medium text-slate-500 text-right">Prompt tokens</th>
                    <th className="px-4 py-2 text-xs font-medium text-slate-500 text-right">Completion tokens</th>
                    <th className="px-4 py-2 text-xs font-medium text-slate-500 text-right">Duration</th>
                    <th className="px-4 py-2 text-xs font-medium text-slate-500 text-left">Summary</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map(r => <RunRow key={r.id} run={r} />)}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>

      {/* Event log */}
      <section aria-labelledby="events-heading">
        <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-200">
            <h2 id="events-heading" className="font-semibold text-slate-900 m-0">
              Event Log
              {events && (
                <span className="ml-2 text-sm font-normal text-slate-500">
                  (last {events.length})
                </span>
              )}
            </h2>
          </div>
          {eventsLoading && (
            <p className="text-slate-500 text-sm px-4 py-3">Loading…</p>
          )}
          {!eventsLoading && (!events || events.length === 0) && (
            <p className="text-slate-500 text-sm px-4 py-3">No events yet.</p>
          )}
          {events && events.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm" aria-label="Event log">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50">
                    <th className="px-4 py-2 text-xs font-medium text-slate-500 text-left">Time</th>
                    <th className="px-4 py-2 text-xs font-medium text-slate-500 text-left">Type</th>
                    <th className="px-4 py-2 text-xs font-medium text-slate-500 text-left">Actor</th>
                    <th className="px-4 py-2 text-xs font-medium text-slate-500 text-left">Task</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map(e => <EventRow key={e.id} event={e} />)}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
