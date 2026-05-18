import { useEffect } from 'react'
import { useProjectStore } from '../../stores/projectStore'
import { Card } from '../shared/Card'

const statDefs = [
  { label: 'Projects', key: 'projects' as const, color: 'text-[#e94560]', border: 'border-t-[#e94560]' },
  { label: 'Sources', key: 'sources' as const, color: 'text-blue-400', border: 'border-t-blue-500' },
  { label: 'Entities', key: 'entities' as const, color: 'text-green-400', border: 'border-t-green-500' },
  { label: 'Claims', key: 'claims' as const, color: 'text-yellow-400', border: 'border-t-yellow-500' },
  { label: 'Reports', key: 'reports' as const, color: 'text-purple-400', border: 'border-t-purple-500' },
]

function StatSkeleton() {
  return (
    <Card>
      <div className="skeleton h-3 w-16 mb-3" />
      <div className="skeleton h-8 w-12" />
    </Card>
  )
}

export function DashboardView() {
  const { stats, projects, fetchStats, fetchProjects } = useProjectStore()

  useEffect(() => {
    fetchStats()
    fetchProjects()
  }, [fetchStats, fetchProjects])

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6">
      <h1 className="text-xl font-bold text-white mb-6">Dashboard</h1>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
        {!stats ? (
          <>
            <StatSkeleton />
            <StatSkeleton />
            <StatSkeleton />
            <StatSkeleton />
            <StatSkeleton />
          </>
        ) : (
          statDefs.map((s) => (
            <Card key={s.label} variant="surface" hover>
              <div className={`border-t-2 ${s.border} -mx-5 -mt-5 mb-3 rounded-t-lg`} style={{ height: 3 }} />
              <div className="text-xs uppercase tracking-wider text-[#8888aa] mb-1">
                {s.label}
              </div>
              <div className={`text-3xl font-bold ${s.color}`}>{stats[s.key]}</div>
            </Card>
          ))
        )}
      </div>

      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Recent Projects</h2>
        <Card variant="surface">
          {projects.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-8">
              <svg className="w-10 h-10 text-[#2a2a4a]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
              </svg>
              <p className="text-sm text-[#8888aa]">
                No projects yet. Start a conversation with the AI or create a project manually.
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {projects.slice(0, 10).map((p) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between py-2.5 px-3 rounded-md hover:bg-[#1a1a2e] transition-colors -mx-3"
                >
                  <div>
                    <div className="text-sm font-medium text-white">{p.name}</div>
                    {p.description && (
                      <div className="text-xs text-[#8888aa] mt-0.5 line-clamp-1">
                        {p.description}
                      </div>
                    )}
                  </div>
                  <div className="text-xs text-[#8888aa]">
                    {new Date(p.created_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
