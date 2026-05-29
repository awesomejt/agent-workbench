import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchProject, fetchSections, createTask } from '../api'

const PHASES = ['discovery', 'design', 'implementation', 'testing', 'review']
const ROLES = [
  'researcher', 'planner', 'implementer', 'writer', 'reviewer', 'tester', 'orchestrator',
]
const MODEL_TIERS = ['local', 'cloud']

function Field({ id, label, required, children, error }) {
  return (
    <div className="space-y-1">
      <label htmlFor={id} className="block text-sm font-medium text-slate-700">
        {label}
        {required && <span className="text-red-500 ml-1" aria-hidden>*</span>}
      </label>
      {children}
      {error && (
        <p role="alert" className="text-xs text-red-600">
          {error}
        </p>
      )}
    </div>
  )
}

function SelectInput({ id, value, onChange, options, placeholder, className = '' }) {
  return (
    <select
      id={id}
      value={value}
      onChange={e => onChange(e.target.value)}
      className={`w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${className}`}
    >
      {placeholder && <option value="">{placeholder}</option>}
      {options.map(o =>
        typeof o === 'string' ? (
          <option key={o} value={o}>{o}</option>
        ) : (
          <option key={o.value} value={o.value}>{o.label}</option>
        ),
      )}
    </select>
  )
}

export default function TaskNew() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [phase, setPhase] = useState('')
  const [role, setRole] = useState('')
  const [modelTier, setModelTier] = useState('')
  const [priority, setPriority] = useState('')
  const [sectionId, setSectionId] = useState('')
  const [durationSeconds, setDurationSeconds] = useState('')
  const [validationExpectations, setValidationExpectations] = useState('')
  const [titleError, setTitleError] = useState('')

  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => fetchProject(projectId),
  })

  const { data: sections } = useQuery({
    queryKey: ['sections', projectId],
    queryFn: () => fetchSections(projectId),
  })

  const sectionOptions = (sections ?? []).map(s => ({
    value: s.id,
    label: s.name ?? s.slug,
  }))

  const { mutate, isPending, error: submitError } = useMutation({
    mutationFn: data => createTask(projectId, data),
    onSuccess: task => {
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] })
      queryClient.invalidateQueries({ queryKey: ['task-count', projectId] })
      navigate(`/projects/${projectId}/tasks/${task.id}`)
    },
  })

  function handleSubmit(e) {
    e.preventDefault()
    if (!title.trim()) {
      setTitleError('Title is required')
      return
    }
    setTitleError('')

    const data = { title: title.trim() }
    if (description.trim()) data.description = description.trim()
    if (phase) data.phase = phase
    if (role) data.role = role
    if (modelTier) data.model_tier = modelTier
    if (priority !== '') {
      const n = parseInt(priority, 10)
      if (!isNaN(n)) data.priority = n
    }
    if (sectionId) data.project_section_id = sectionId
    if (durationSeconds !== '') {
      const n = parseInt(durationSeconds, 10)
      if (!isNaN(n) && n > 0) data.estimated_duration_seconds = n
    }
    if (validationExpectations.trim()) data.validation_expectations = validationExpectations.trim()

    mutate(data)
  }

  return (
    <div className="max-w-2xl space-y-6">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="text-sm text-slate-500">
        <Link to="/" className="hover:text-indigo-700">Projects</Link>
        <span className="mx-2">›</span>
        <Link to={`/projects/${projectId}`} className="hover:text-indigo-700">
          {project?.name ?? projectId.slice(0, 8) + '…'}
        </Link>
        <span className="mx-2">›</span>
        <span className="text-slate-900 font-medium">New Task</span>
      </nav>

      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-6 m-0">Add Task</h2>

        {submitError && (
          <p role="alert" className="text-red-700 bg-red-50 border border-red-200 rounded p-3 text-sm mb-4">
            {submitError.message}
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-5" noValidate>
          <Field id="title" label="Title" required error={titleError}>
            <input
              id="title"
              type="text"
              value={title}
              onChange={e => { setTitle(e.target.value); if (titleError) setTitleError('') }}
              placeholder="e.g. Implement X feature"
              aria-required="true"
              className="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </Field>

          <Field id="description" label="Description">
            <textarea
              id="description"
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={4}
              placeholder="Optional task description…"
              className="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-y"
            />
          </Field>

          <div className="grid grid-cols-2 gap-4">
            <Field id="phase" label="Phase">
              <SelectInput
                id="phase"
                value={phase}
                onChange={setPhase}
                options={PHASES}
                placeholder="Select phase…"
              />
            </Field>

            <Field id="role" label="Role">
              <SelectInput
                id="role"
                value={role}
                onChange={setRole}
                options={ROLES}
                placeholder="Select role…"
              />
            </Field>

            <Field id="model-tier" label="Model tier">
              <SelectInput
                id="model-tier"
                value={modelTier}
                onChange={setModelTier}
                options={MODEL_TIERS}
                placeholder="Select tier…"
              />
            </Field>

            <Field id="priority" label="Priority">
              <input
                id="priority"
                type="number"
                value={priority}
                onChange={e => setPriority(e.target.value)}
                min={0}
                max={999}
                placeholder="e.g. 50"
                className="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </Field>

            <Field id="section" label="Section">
              <SelectInput
                id="section"
                value={sectionId}
                onChange={setSectionId}
                options={sectionOptions}
                placeholder="None (project-wide)"
              />
            </Field>

            <Field id="duration" label="Duration (seconds)">
              <input
                id="duration"
                type="number"
                value={durationSeconds}
                onChange={e => setDurationSeconds(e.target.value)}
                min={0}
                placeholder="e.g. 1800"
                className="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </Field>
          </div>

          <Field id="validation" label="Validation expectations">
            <textarea
              id="validation"
              value={validationExpectations}
              onChange={e => setValidationExpectations(e.target.value)}
              rows={2}
              placeholder="e.g. Tests pass, build succeeds…"
              className="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-y"
            />
          </Field>

          <div className="flex items-center justify-end gap-3 pt-2">
            <Link
              to={`/projects/${projectId}`}
              className="text-sm text-slate-600 hover:text-slate-900 no-underline px-4 py-2 rounded border border-slate-300 hover:bg-slate-50"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={isPending}
              className="text-sm bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isPending ? 'Creating…' : 'Create task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
