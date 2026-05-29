import { Routes, Route, NavLink, Outlet } from 'react-router-dom'
import ProjectList from './routes/ProjectList'
import ProjectDetail from './routes/ProjectDetail'
import ProjectRuns from './routes/ProjectRuns'
import TaskDetail from './routes/TaskDetail'
import TaskNew from './routes/TaskNew'
import AgentRegistry from './routes/AgentRegistry'
import styles from './App.module.css'

function Layout() {
  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <div className="flex items-center gap-6">
          <NavLink to="/" className="text-white no-underline">
            <h1 className="m-0 text-xl font-semibold tracking-tight">Agent Workbench</h1>
          </NavLink>
          <NavLink
            to="/agents"
            className={({ isActive }) =>
              `text-sm no-underline ${isActive ? 'text-white font-medium' : 'text-slate-300 hover:text-white'}`
            }
          >
            Agents
          </NavLink>
        </div>
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
        <Route path="projects/:projectId/runs" element={<ProjectRuns />} />
        <Route path="projects/:projectId/tasks/new" element={<TaskNew />} />
        <Route path="projects/:projectId/tasks/:taskId" element={<TaskDetail />} />
        <Route path="agents" element={<AgentRegistry />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
