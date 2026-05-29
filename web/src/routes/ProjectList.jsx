import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useQueries } from '@tanstack/react-query'
import {
  fetchProjects,
  fetchProjectStatus,
  fetchTaskCount,
} from '../api'
import PhaseBadge from '../components/PhaseBadge'

const STATUS_COUNTS = ['pending', 'in_progress', 'blocked']

const COUNT_STYLES = {
  pending: 'bg-slate-100 text-slate-600',
  in_progress: 'bg-indigo-100 text-indigo-700',
  blocked: 'bg-red-100 text-red-600',
}

const COUNT_LABELS = {
  pending: 'pending',
  in_progress: 'active',
  blocked: 'blocked',
}

function ProjectRow({ project }) {
  const { data: latestStatus } = useQuery({
    queryKey: ['project-status', project.id],
    queryFn: () => fetchProjectStatus(project.id),
  })

  const countResults = useQueries({
    queries: STATUS_COUNTS.map(s => ({
      queryKey: ['task-count', project.id, s],
      queryFn: () => fetchTaskCount(project.id, s),
    })),
  })

  return (
    <li className="flex items-center gap-3 px-4 py-3 bg-white border border-slate-200 rounded-md hover:border-slate-300 hover:bg-slate-50 transition-colors">
      <Link
        to={`/projects/${project.id}`}
        className="flex-1 flex items-center gap-3 no-underline"
        aria-label={`Open project ${project.name}`}
      >
        <span className="font-mono text-sm text-slate-500 shrink-0 w-48 truncate">
          {project.slug}
        </span>
        <span className="font-medium text-slate-900 flex-1 truncate">
          {project.name}
        </span>
      </Link>
      <div className="flex items-center gap-2 shrink-0">
        {STATUS_COUNTS.map((s, i) => {
          const count = countResults[i].data
          if (!count) return null
          return (
            <span
              key={s}
              className={`px-1.5 py-0.5 rounded text-xs font-mono ${COUNT_STYLES[s]}`}
              title={`${count} ${s}`}
            >
              {count} {COUNT_LABELS[s]}
            </span>
          )
        })}
        <PhaseBadge phase={latestStatus?.phase} />
        <span className="text-xs text-slate-400 font-mono shrink-0">
          {project.project_type}
        </span>
      </div>
    </li>
  )
}

export default function ProjectList() {
  const [nameFilter, setNameFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [sortBy, setSortBy] = useState('name')

  const { data: projects, error, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: fetchProjects,
  })

  const projectTypes = [
    ...new Set((projects ?? []).map(p => p.project_type).filter(Boolean)),
  ].sort()

  const filtered = (projects ?? [])
    .filter(
      p =>
        !nameFilter ||
        p.name.toLowerCase().includes(nameFilter.toLowerCase()) ||
        p.slug.toLowerCase().includes(nameFilter.toLowerCase()),
    )
    .filter(p => !typeFilter || p.project_type === typeFilter)
    .sort((a, b) => {
      if (sortBy === 'slug') return a.slug.localeCompare(b.slug)
      return a.name.localeCompare(b.name)
    })

  return (
    <div>
      <div className="flex items-center justify-between mb-6 gap-4 flex-wrap">
        <h2 className="text-lg font-semibold text-slate-900 m-0">Projects</h2>
        <div className="flex items-center gap-3 flex-wrap">
          <input
            type="search"
            placeholder="Filter by name or slug…"
            value={nameFilter}
            onChange={e => setNameFilter(e.target.value)}
            className="text-sm border border-slate-300 rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 min-w-52"
          />
          <select
            value={typeFilter}
            onChange={e => setTypeFilter(e.target.value)}
            aria-label="Filter by type"
            className="text-sm border border-slate-300 rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All types</option>
            {projectTypes.map(t => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            aria-label="Sort projects"
            className="text-sm border border-slate-300 rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="name">Sort: name</option>
            <option value="slug">Sort: slug</option>
          </select>
        </div>
      </div>

      {error && (
        <p
          role="alert"
          className="text-red-700 bg-red-50 border border-red-200 rounded p-3 text-sm mb-4"
        >
          Could not load projects: {error.message}
        </p>
      )}

      {isLoading && (
        <p className="text-slate-500" aria-live="polite">
          Loading…
        </p>
      )}

      {!isLoading && projects !== undefined && filtered.length === 0 && (
        <p className="text-slate-500">No projects found.</p>
      )}

      {filtered.length > 0 && (
        <ul
          className="flex flex-col gap-2 list-none p-0 m-0"
          aria-label="Project list"
        >
          {filtered.map(p => (
            <ProjectRow key={p.id} project={p} />
          ))}
        </ul>
      )}
    </div>
  )
}
