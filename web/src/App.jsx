import { Routes, Route, NavLink, Outlet } from 'react-router-dom'
import ProjectList from './routes/ProjectList'
import ProjectDetail from './routes/ProjectDetail'
import styles from './App.module.css'

function Layout() {
  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <NavLink to="/" className="text-white no-underline">
          <h1 className="m-0 text-xl font-semibold tracking-tight">Agent Workbench</h1>
        </NavLink>
      </header>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}

function NotFound() {
  return <p className="text-slate-500">Page not found.</p>
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<ProjectList />} />
        <Route path="projects/:projectId" element={<ProjectDetail />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
