import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchAgents } from '../api'

const TIER_COLORS = {
  cloud: 'bg-indigo-100 text-indigo-700',
  local: 'bg-slate-100 text-slate-600',
}

export default function AgentRegistry() {
  const { data: agents, error, isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: fetchAgents,
  })

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="text-sm text-slate-500">
        <Link to="/" className="hover:text-indigo-700">Projects</Link>
        <span className="mx-2">›</span>
        <span className="text-slate-900 font-medium">Agent Registry</span>
      </nav>

      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-200">
          <h2 className="font-semibold text-slate-900 m-0">
            Agents
            {agents && (
              <span className="ml-2 text-sm font-normal text-slate-500">({agents.length})</span>
            )}
          </h2>
        </div>

        {error && (
          <p role="alert" className="text-red-700 bg-red-50 border-b border-red-200 p-4 text-sm m-0">
            Could not load agents: {error.message}
          </p>
        )}

        {isLoading && (
          <p className="text-slate-500 text-sm px-4 py-3">Loading…</p>
        )}

        {!isLoading && agents !== undefined && agents.length === 0 && (
          <p className="text-slate-500 text-sm px-4 py-3">No agents registered.</p>
        )}

        {agents && agents.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm" aria-label="Agent registry">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="px-4 py-2 text-xs font-medium text-slate-500 text-left">Name</th>
                  <th className="px-4 py-2 text-xs font-medium text-slate-500 text-left">Type</th>
                  <th className="px-4 py-2 text-xs font-medium text-slate-500 text-left">Model</th>
                  <th className="px-4 py-2 text-xs font-medium text-slate-500 text-left">Tier</th>
                  <th className="px-4 py-2 text-xs font-medium text-slate-500 text-left">Capabilities</th>
                  <th className="px-4 py-2 text-xs font-medium text-slate-500 text-left">Notes</th>
                </tr>
              </thead>
              <tbody>
                {agents.map(a => (
                  <tr key={a.id} className="border-b border-slate-100 hover:bg-slate-50 last:border-0">
                    <td className="px-4 py-2.5 font-mono text-sm text-slate-900 font-medium">
                      {a.name}
                    </td>
                    <td className="px-4 py-2.5 text-xs text-slate-500">
                      {a.agent_type ?? '—'}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs text-slate-600">
                      {a.default_model ?? '—'}
                    </td>
                    <td className="px-4 py-2.5">
                      {a.model_tier ? (
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${TIER_COLORS[a.model_tier] ?? 'bg-slate-100 text-slate-600'}`}
                        >
                          {a.model_tier}
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-2.5 text-xs text-slate-500 max-w-xs truncate">
                      {Array.isArray(a.capabilities) ? a.capabilities.join(', ') : (a.capabilities ?? '—')}
                    </td>
                    <td className="px-4 py-2.5 text-xs text-slate-400 max-w-xs truncate">
                      {a.runtime_notes ?? ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
