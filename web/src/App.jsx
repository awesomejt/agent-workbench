import { useEffect, useState } from 'react'
import styles from './App.module.css'

function App() {
  const [projects, setProjects] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/projects')
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(data => setProjects(Array.isArray(data) ? data : data.items ?? []))
      .catch(err => setError(err.message))
  }, [])

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <h1>Agent Workbench</h1>
      </header>

      <main className={styles.main}>
        <section aria-labelledby="projects-heading">
          <h2 id="projects-heading">Projects</h2>

          {error && (
            <p role="alert" className={styles.error}>
              Could not load projects: {error}
            </p>
          )}

          {!error && projects === null && (
            <p aria-live="polite">Loading…</p>
          )}

          {projects !== null && projects.length === 0 && (
            <p>No projects found.</p>
          )}

          {projects !== null && projects.length > 0 && (
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
      </main>
    </div>
  )
}

export default App
