import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchTask, updateTask, completeTask, fetchRelationships } from '../api'
import PhaseBadge from '../components/PhaseBadge'
import { TaskStatusBadge } from '../components/StatusBadge'

const PHASES = ['discovery', 'design', 'implementation', 'testing', 'review']

const REL_LABELS = {
  blocks: 'Blocks',
  blocked_by: 'Blocked by',
  subtask_of: 'Subtask of',
  duplicates: 'Duplicates',
}

function Field({ label, value, mono }) {
  if (value == null || value === '') return null
  return (
    <div className="flex gap-2 py-1.5 border-b border-slate-100 last:border-0 text-sm">
      <span className="text-slate-500 w-40 shrink-0">{label}</span>
      <span className={`text-slate-900 flex-1 ${mono ? 'font-mono text-xs break-all' : ''}`}>
        {value}
      </span>
    </div>
  )
}

function RelationshipsSection({ taskId }) {
  const { data: rels, isLoading } = useQuery({
    queryKey: ['task-relationships', taskId],
    queryFn: () => fetchRelationships(taskId),
  })

  if (isLoading) return <p className="text-slate-400 text-xs">Loading…</p>
  if (!rels || rels.length === 0)
    return <p className="text-slate-400 text-sm">None.</p>

  const grouped = rels.reduce((acc, r) => {
    const type = r.relationship_type
    if (!acc[type]) acc[type] = []
    acc[type].push(r)
    return acc
  }, {})

  return (
    <div className="space-y-3">
      {Object.entries(grouped).map(([type, items]) => (
        <div key={type}>
          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
            {REL_LABELS[type] ?? type}
          </h4>
          <ul className="list-none p-0 m-0 space-y-1">
            {items.map(rel => {
              const otherId =
                rel.from_task_id === taskId ? rel.to_task_id : rel.from_task_id
              return (
                <li key={rel.id} className="text-sm">
                  <span className="font-mono text-xs text-slate-400">{otherId}</span>
                </li>
              )
            })}
          </ul>
        </div>
      ))}
    </div>
  )
}

function EditForm({ task, onCancel, onSaved }) {
  const queryClient = useQueryClient()
  const [title, setTitle] = useState(task.title)
  const [description, setDescription] = useState(task.description ?? '')
  const [phase, setPhase] = useState(task.phase ?? '')
  const [priority, setPriority] = useState(task.priority != null ? String(task.priority) : '')

  const { mutate, isPending, error } = useMutation({
    mutationFn: data => updateTask(task.id, data),
    onSuccess: updated => {
      queryClient.setQueryData(['task', task.id], updated)
      queryClient.invalidateQueries({ queryKey: ['tasks', task.project_id] })
      onSaved(updated)
    },
  })

  function handleSubmit(e) {
    e.preventDefault()
    const data = { title: title.trim(), version: task.version }
    if (description.trim() !== (task.description ?? '')) data.description = description.trim()
    if (phase !== (task.phase ?? '')) data.phase = phase || null
    const p = priority !== '' ? parseInt(priority, 10) : null
    if (p !== task.priority) data.priority = p
    mutate(data)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <p role="alert" className="text-red-700 bg-red-50 border border-red-200 rounded p-3 text-sm">
          {error.message}
        </p>
      )}
      <div>
        <label htmlFor="edit-title" className="block text-sm font-medium text-slate-700 mb-1">
          Title <span className="text-red-500">*</span>
        </label>
        <input
          id="edit-title"
          type="text"
          value={title}
          onChange={e => setTitle(e.target.value)}
          required
          className="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>
      <div>
        <label htmlFor="edit-description" className="block text-sm font-medium text-slate-700 mb-1">
          Description
        </label>
        <textarea
          id="edit-description"
          value={description}
          onChange={e => setDescription(e.target.value)}
          rows={4}
          className="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-y"
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="edit-phase" className="block text-sm font-medium text-slate-700 mb-1">Phase</label>
          <select
            id="edit-phase"
            value={phase}
            onChange={e => setPhase(e.target.value)}
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">None</option>
            {PHASES.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="edit-priority" className="block text-sm font-medium text-slate-700 mb-1">Priority</label>
          <input
            id="edit-priority"
            type="number"
            value={priority}
            onChange={e => setPriority(e.target.value)}
            min={0}
            max={999}
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>
      <div className="flex items-center justify-end gap-3 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="text-sm text-slate-600 hover:text-slate-900 px-4 py-2 rounded border border-slate-300 hover:bg-slate-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isPending || !title.trim()}
          className="text-sm bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          {isPending ? 'Saving…' : 'Save changes'}
        </button>
      </div>
    </form>
  )
}

function StatusTransitions({ task }) {
  const queryClient = useQueryClient()

  const invalidateAfterTransition = updated => {
    queryClient.setQueryData(['task', task.id], updated)
    queryClient.invalidateQueries({ queryKey: ['tasks', task.project_id] })
    queryClient.invalidateQueries({ queryKey: ['task-count', task.project_id] })
    queryClient.invalidateQueries({ queryKey: ['events', task.project_id] })
  }

  const refetchTask = () =>
    queryClient.invalidateQueries({ queryKey: ['task', task.id] })

  const unblockMutation = useMutation({
    mutationFn: () => updateTask(task.id, { status: 'pending', version: task.version }),
    onSuccess: invalidateAfterTransition,
    onError: refetchTask,
  })

  const completeMutation = useMutation({
    mutationFn: () => completeTask(task.id, { agentName: task.claimed_by }),
    onSuccess: invalidateAfterTransition,
    onError: refetchTask,
  })

  const err = unblockMutation.error ?? completeMutation.error

  if (task.status !== 'blocked' && task.status !== 'in_progress') return null

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5">
      <h3 className="text-sm font-semibold text-slate-900 mb-3">Status Actions</h3>
      {err && (
        <p role="alert" className="text-red-700 bg-red-50 border border-red-200 rounded p-2 text-xs mb-3">
          {err.message}
        </p>
      )}
      <div className="flex gap-3 flex-wrap">
        {task.status === 'blocked' && (
          <button
            onClick={() => unblockMutation.mutate()}
            disabled={unblockMutation.isPending}
            className="text-sm bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded hover:bg-slate-50 hover:border-slate-400 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {unblockMutation.isPending ? 'Unblocking…' : 'Unblock → pending'}
          </button>
        )}
        {task.status === 'in_progress' && (
          <button
            onClick={() => completeMutation.mutate()}
            disabled={completeMutation.isPending}
            className="text-sm bg-emerald-600 text-white px-4 py-2 rounded hover:bg-emerald-700 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            {completeMutation.isPending ? 'Completing…' : 'Mark completed'}
          </button>
        )}
      </div>
    </div>
  )
}

export default function TaskDetail() {
  const { projectId, taskId } = useParams()
  const [editing, setEditing] = useState(false)

  const { data: task, error, isLoading } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => fetchTask(taskId),
  })

  if (isLoading) {
    return <p className="text-slate-500" aria-live="polite">Loading…</p>
  }

  if (error) {
    return (
      <p role="alert" className="text-red-700 bg-red-50 border border-red-200 rounded p-3 text-sm">
        Could not load task: {error.message}
      </p>
    )
  }

  if (!task) return null

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="text-sm text-slate-500">
        <Link to="/" className="hover:text-indigo-700">Projects</Link>
        <span className="mx-2">›</span>
        <Link to={`/projects/${projectId}`} className="hover:text-indigo-700">
          {projectId.slice(0, 8)}…
        </Link>
        <span className="mx-2">›</span>
        <span className="text-slate-900 font-medium truncate">{task.title}</span>
      </nav>

      {/* Task header / edit form */}
      <div className="bg-white border border-slate-200 rounded-lg p-5">
        {editing ? (
          <EditForm
            task={task}
            onCancel={() => setEditing(false)}
            onSaved={() => setEditing(false)}
          />
        ) : (
          <>
            <div className="flex items-start gap-4 mb-3">
              <h2 className="text-xl font-semibold text-slate-900 flex-1 m-0">{task.title}</h2>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => setEditing(true)}
                  className="text-xs text-slate-500 hover:text-slate-900 border border-slate-200 px-3 py-1.5 rounded hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  Edit
                </button>
                <TaskStatusBadge status={task.status} />
                <PhaseBadge phase={task.phase} />
              </div>
            </div>

            {task.description && (
              <p className="text-sm text-slate-700 mb-4 m-0 whitespace-pre-wrap">{task.description}</p>
            )}

            <div className="divide-y divide-slate-100">
              <Field label="Priority" value={task.priority} />
              <Field label="Role" value={task.role} mono />
              <Field label="Model tier" value={task.model_tier} mono />
              <Field label="Assignee type" value={task.assignee_type} />
              <Field label="Assignee name" value={task.assignee_name} />
            </div>
          </>
        )}
      </div>

      {/* Status transitions */}
      <StatusTransitions task={task} />

      {/* Lease state */}
      {task.claimed_by && (
        <div className="bg-white border border-slate-200 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-900 mb-3">Lease</h3>
          <div className="divide-y divide-slate-100">
            <Field label="Claimed by" value={task.claimed_by} mono />
            <Field label="Claimed until" value={task.claimed_until} mono />
            <Field label="Lease version" value={task.lease_version} />
          </div>
        </div>
      )}

      {/* Validation & Evidence */}
      {(task.validation_expectations || task.completion_evidence) && (
        <div className="bg-white border border-slate-200 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-slate-900 mb-3">Validation</h3>
          {task.validation_expectations && (
            <div className="mb-3">
              <p className="text-xs text-slate-500 font-semibold uppercase tracking-wide mb-1">
                Expectations
              </p>
              <p className="text-sm text-slate-700 m-0 whitespace-pre-wrap">
                {task.validation_expectations}
              </p>
            </div>
          )}
          {task.completion_evidence && (
            <div>
              <p className="text-xs text-slate-500 font-semibold uppercase tracking-wide mb-1">
                Completion evidence
              </p>
              <p className="text-sm text-slate-700 m-0 whitespace-pre-wrap">
                {task.completion_evidence}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Relationships */}
      <div className="bg-white border border-slate-200 rounded-lg p-5">
        <h3 className="text-sm font-semibold text-slate-900 mb-3">Relationships</h3>
        <RelationshipsSection taskId={taskId} />
      </div>

      {/* Metadata */}
      <div className="bg-white border border-slate-200 rounded-lg p-5">
        <h3 className="text-sm font-semibold text-slate-900 mb-3">Metadata</h3>
        <div className="divide-y divide-slate-100">
          <Field label="Task ID" value={task.id} mono />
          <Field label="Project ID" value={task.project_id} mono />
          <Field label="Section ID" value={task.project_section_id} mono />
          <Field label="Created" value={new Date(task.created_at).toLocaleString()} />
          <Field label="Updated" value={new Date(task.updated_at).toLocaleString()} />
          <Field label="Version" value={task.version} />
        </div>
      </div>
    </div>
  )
}
