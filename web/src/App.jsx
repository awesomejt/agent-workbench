import { Routes, Route, NavLink, Outlet } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import styles from './App.module.css'

function fetchProjects() {
  return fetch('/api/projects')
    .then(r => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      return r.json()
    })
    .then(data => (Array.isArray(data) ? data : (data.items ?? [])))
}

function ProjectList() {
  const { data: projects, error, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: fetchProjects,
  })

  return (
    <section aria-labelledby="projects-heading">
      <h2 id="projects-heading">Projects</h2>

      {error && (
        <p role="alert" className={styles.error}>
          Could not load projects: {error.message}
        </p>
      )}

      {isLoading && <p aria-live="polite">Loading…</p>}

      {projects !== undefined && projects.length === 0 && (
        <p>No projects found.</p>
      )}

      {projects !== undefined && projects.length > 0 && (
        <ul className={styles.projectList}>
          {projects.map(p => (
            <li key={p.id} className={styles.projectItem}>
              <span className={styles.projectSlug}>{p.slug}</span>
              <span className={styles.projectName}>{p.name}</span>
              {p.phase && (
                <span className={styles.projectPhase}>{p.phase}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function Layout() {
  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <h1>Agent Workbench</h1>
      </header>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<ProjectList />} />
      </Route>
    </Routes>
  )
}
