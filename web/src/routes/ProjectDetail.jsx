import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  fetchProject,
  fetchProjectStatus,
  fetchTasks,
  fetchEvents,
} from '../api'
import PhaseBadge from '../components/PhaseBadge'
import { ProjectStatusBadge, TaskStatusBadge } from '../components/StatusBadge'

const TASK_STATUS_OPTIONS = [
  { value: '', label: 'All (non-completed)' },
  { value: 'pending', label: 'Pending' },
  { value: 'in_progress', label: 'Active' },
  { value: 'blocked', label: 'Blocked' },
  { value: 'completed', label: 'Completed' },
]

const PHASE_OPTIONS = [
  '', 'discovery', 'design', 'implementation', 'testing', 'review',
]

function MetaRow({ label, value }) {
  if (!value) return null
  return (
    <div className="flex gap-2 text-sm">
      <span className="text-slate-500 w-32 shrink-0">{label}</span>
      <span className="text-slate-900 font-mono break-all">{value}</span>
    </div>
  )
}

function TaskRow({ task }) {
  return (
    <li className="flex items-start gap-3 px-3 py-2.5 border-b border-slate-100 last:border-0 hover:bg-slate-50">
      <div className="flex-1 min-w-0">
        <Link
          to={`/projects/${task.project_id}/tasks/${task.id}`}
          className="text-sm font-medium text-slate-900 hover:text-indigo-700 no-underline truncate block"
        >
          {task.title}
        </Link>
        {task.claimed_by && (
          <p className="text-xs text-slate-400 mt-0.5 m-0">
            claimed by {task.claimed_by}
          </p>
        )}
      </div>
      <div className="flex items-center gap-1.5 shrink-0">
        {task.phase && (
          <span className="text-xs text-slate-400 font-mono">{task.phase}</span>
        )}
        <TaskStatusBadge status={task.status} />
        {task.priority != null && (
          <span className="text-xs text-slate-300 font-mono w-6 text-right">
            {task.priority}
          </span>
        )}
      </div>
    </li>
  )
}

function EventRow({ event }) {
  const ts = new Date(event.created_at)
  const timeStr = ts.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  const dateStr = ts.toLocaleDateString([], { month: 'short', day: 'numeric' })

  return (
    <li className="flex gap-3 py-2 border-b border-slate-100 last:border-0 text-sm">
      <div className="text-xs text-slate-400 shrink-0 w-20 pt-0.5">
        <div>{dateStr}</div>
        <div>{timeStr}</div>
      </div>
      <div className="flex-1 min-w-0">
        <span className="font-mono text-xs text-indigo-600 mr-2">
          {event.event_type}
        </span>
        {event.actor_name && (
          <span className="text-slate-500 text-xs">{event.actor_name}</span>
        )}
      </div>
    </li>
  )
}

export default function ProjectDetail() {
  const { projectId } = useParams()
  const [statusFilter, setStatusFilter] = useState('')
  const [phaseFilter, setPhaseFilter] = useState('')
  const [sortBy, setSortBy] = useState('priority')

  const { data: project, error: projectError, isLoading: projectLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => fetchProject(projectId),
  })

  const { data: latestStatus } = useQuery({
    queryKey: ['project-status', projectId],
    queryFn: () => fetchProjectStatus(projectId),
  })

  const { data: allTasks, isLoading: tasksLoading } = useQuery({
    queryKey: ['tasks', projectId],
    queryFn: () => fetchTasks(projectId, { perPage: 100 }),
  })

  const { data: events } = useQuery({
    queryKey: ['events', projectId],
    queryFn: () => fetchEvents(projectId, { perPage: 10 }),
  })

  if (projectLoading) {
    return <p className="text-slate-500" aria-live="polite">Loading…</p>
  }

  if (projectError) {
    return (
      <p role="alert" className="text-red-700 bg-red-50 border border-red-200 rounded p-3 text-sm">
        Could not load project: {projectError.message}
      </p>
    )
  }

  if (!project) return null

  const tasks = (allTasks ?? [])
    .filter(t => {
      if (!statusFilter) return t.status !== 'completed' && t.status !== 'duplicate' && t.status !== 'rejected'
      return t.status === statusFilter
    })
    .filter(t => !phaseFilter || t.phase === phaseFilter)
    .sort((a, b) => {
      if (sortBy === 'priority') return (b.priority ?? 0) - (a.priority ?? 0)
      if (sortBy === 'status') return a.status.localeCompare(b.status)
      if (sortBy === 'phase') return (a.phase ?? '').localeCompare(b.phase ?? '')
      return a.title.localeCompare(b.title)
    })

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="text-sm text-slate-500">
        <Link to="/" className="hover:text-indigo-700">Projects</Link>
        <span className="mx-2">›</span>
        <span className="text-slate-900 font-medium">{project.name}</span>
      </nav>

      {/* Project header */}
      <div className="bg-white border border-slate-200 rounded-lg p-5">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <h2 className="text-xl font-semibold text-slate-900 m-0">{project.name}</h2>
            <p className="text-sm font-mono text-slate-500 mt-1 m-0">{project.slug}</p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Link
              to={`/projects/${projectId}/runs`}
              className="text-xs text-slate-500 hover:text-indigo-700 border border-slate-200 px-3 py-1.5 rounded hover:bg-slate-50 no-underline"
            >
              Runs & Events
            </Link>
            {latestStatus && <ProjectStatusBadge status={latestStatus.status} />}
            {latestStatus && <PhaseBadge phase={latestStatus.phase} />}
          </div>
        </div>

        {latestStatus?.summary && (
          <p className="text-sm text-slate-600 mb-4 m-0">{latestStatus.summary}</p>
        )}

        <div className="space-y-1.5">
          <MetaRow label="Type" value={project.project_type} />
          <MetaRow label="Environment" value={project.environment} />
          <MetaRow label="Default agent" value={project.default_agent} />
          <MetaRow label="Git remote" value={project.git_remote_url} />
          <MetaRow label="Local path" value={project.local_path} />
        </div>
      </div>

      {/* Tasks and Events side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Task list — takes 2/3 */}
        <section className="lg:col-span-2" aria-labelledby="tasks-heading">
          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200">
              <h3 id="tasks-heading" className="font-semibold text-slate-900 m-0">
                Tasks
                {allTasks && (
                  <span className="ml-2 text-sm font-normal text-slate-500">
                    ({tasks.length})
                  </span>
                )}
              </h3>
              <Link
                to={`/projects/${projectId}/tasks/new`}
                className="text-xs bg-indigo-600 text-white px-3 py-1.5 rounded hover:bg-indigo-700 no-underline"
              >
                + Add task
              </Link>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-2 px-4 py-2 bg-slate-50 border-b border-slate-200 flex-wrap">
              <select
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
                aria-label="Filter by status"
                className="text-xs border border-slate-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {TASK_STATUS_OPTIONS.map(o => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
              <select
                value={phaseFilter}
                onChange={e => setPhaseFilter(e.target.value)}
                aria-label="Filter by phase"
                className="text-xs border border-slate-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All phases</option>
                {PHASE_OPTIONS.filter(Boolean).map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
              <select
                value={sortBy}
                onChange={e => setSortBy(e.target.value)}
                aria-label="Sort tasks"
                className="text-xs border border-slate-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="priority">Sort: priority</option>
                <option value="status">Sort: status</option>
                <option value="phase">Sort: phase</option>
                <option value="title">Sort: title</option>
              </select>
            </div>

            {tasksLoading && (
              <p className="text-slate-500 text-sm px-4 py-3">Loading tasks…</p>
            )}

            {!tasksLoading && tasks.length === 0 && (
              <p className="text-slate-500 text-sm px-4 py-3">No tasks found.</p>
            )}

            {tasks.length > 0 && (
              <ul className="list-none p-0 m-0" aria-label="Task list">
                {tasks.map(t => <TaskRow key={t.id} task={t} />)}
              </ul>
            )}
          </div>
        </section>

        {/* Events sidebar — takes 1/3 */}
        <section aria-labelledby="events-heading">
          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-200">
              <h3 id="events-heading" className="font-semibold text-slate-900 m-0">
                Recent Events
              </h3>
            </div>
            {!events || events.length === 0 ? (
              <p className="text-slate-500 text-sm px-4 py-3">No events yet.</p>
            ) : (
              <ul className="list-none p-0 m-0 px-4" aria-label="Event log">
                {events.map(e => <EventRow key={e.id} event={e} />)}
              </ul>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}
