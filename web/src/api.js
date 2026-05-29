async function apiFetch(url) {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export function fetchProjects({ perPage = 100 } = {}) {
  return apiFetch(`/api/projects?per_page=${perPage}`).then(d => d.items ?? [])
}

export function fetchProject(projectId) {
  return apiFetch(`/api/projects/${projectId}`)
}

export function fetchProjectStatus(projectId) {
  return apiFetch(`/api/projects/${projectId}/status?per_page=1`).then(
    d => d.items?.[0] ?? null,
  )
}

export function fetchTaskCount(projectId, status) {
  return apiFetch(
    `/api/projects/${projectId}/tasks?status=${encodeURIComponent(status)}&per_page=1`,
  ).then(d => d.total ?? 0)
}

export function fetchTasks(projectId, { status, perPage = 50 } = {}) {
  const params = new URLSearchParams({ per_page: perPage })
  if (status) params.set('status', status)
  return apiFetch(`/api/projects/${projectId}/tasks?${params}`).then(
    d => d.items ?? [],
  )
}

export function fetchTask(taskId) {
  return apiFetch(`/api/tasks/${taskId}`)
}

export function fetchEvents(projectId, { perPage = 20 } = {}) {
  return apiFetch(
    `/api/projects/${projectId}/events?per_page=${perPage}`,
  ).then(d => d.items ?? [])
}

export function fetchAgents({ perPage = 100 } = {}) {
  return apiFetch(`/api/agents?per_page=${perPage}`).then(d => d.items ?? [])
}

// NOTE: no GET /api/runs list endpoint exists yet. fetchRuns is a stub.
// See AWB task for adding GET /api/projects/:id/runs.
export function fetchRuns(_projectId, _opts = {}) {
  return Promise.resolve([])
}
