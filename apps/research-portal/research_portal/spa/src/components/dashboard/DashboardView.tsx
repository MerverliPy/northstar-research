import { useEffect } from 'react'
import { useProjectStore } from '../../stores/projectStore'
import { Card } from '../shared/Card'

export function DashboardView() {
  const { stats, projects, fetchStats, fetchProjects } = useProjectStore()

  useEffect(() => {
    fetchStats()
    fetchProjects()
  }, [fetchStats, fetchProjects])

  const statCards = [
    { label: 'Projects', value: stats?.projects ?? '-', color: 'text-[#e94560]' },
    { label: 'Sources', value: stats?.sources ?? '-', color: 'text-blue-400' },
    { label: 'Entities', value: stats?.entities ?? '-', color: 'text-green-400' },
    { label: 'Claims', value: stats?.claims ?? '-', color: 'text-yellow-400' },
    { label: 'Reports', value: stats?.reports ?? '-', color: 'text-purple-400' },
  ]

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6">
      <h1 className="text-xl font-bold text-white mb-6">Dashboard</h1>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
        {statCards.map((stat) => (
          <Card key={stat.label}>
            <div className="text-xs uppercase tracking-wider text-[#8888aa] mb-1">
              {stat.label}
            </div>
            <div className={`text-3xl font-bold ${stat.color}`}>{stat.value}</div>
          </Card>
        ))}
      </div>

      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Recent Projects</h2>
        <Card>
          {projects.length === 0 ? (
            <p className="text-[#8888aa] text-sm py-4 text-center">
              No projects yet. Start a conversation with the AI or create a project manually.
            </p>
          ) : (
            <div className="space-y-3">
              {projects.slice(0, 10).map((p) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between py-2 border-b border-[#2a2a4a]/50 last:border-0"
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
