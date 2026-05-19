import { useEffect, useState, useRef, useCallback } from 'react'
import { useProjectStore } from '../../stores/projectStore'
import { Card } from '../shared/Card'
import type { GraphData } from '../../types'

function GraphSkeleton() {
  return (
    <div className="flex items-center justify-center h-full p-8">
      <div className="flex flex-col items-center gap-4 w-full max-w-xs">
        <div className="flex gap-4">
          <div className="skeleton w-12 h-12 rounded-full" />
          <div className="skeleton w-16 h-16 rounded-full" />
          <div className="skeleton w-10 h-10 rounded-full" />
        </div>
        <div className="flex gap-3">
          <div className="skeleton w-14 h-14 rounded-full" />
          <div className="skeleton w-12 h-12 rounded-full" />
        </div>
        <div className="skeleton h-3 w-24 mt-2" />
      </div>
    </div>
  )
}

export function GraphViewer() {
  const { projects, fetchProjects } = useProjectStore()
  const [selectedProject, setSelectedProject] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const networkRef = useRef<any>(null)

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  const loadGraph = useCallback(async (projectId: string) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/v1/graph/data/${projectId}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data: GraphData = await res.json()

      if (!containerRef.current) return

      containerRef.current.innerHTML = ''

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const vis = (await import('vis-network/standalone')) as any
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const DataSet = (vis.DataSet || (window as any).vis?.DataSet) as any

      const nodes = new DataSet(
        data.nodes.map((n) => ({
          id: n.id,
          label: n.label,
          group: n.group,
          title: n.title || n.label,
        }))
      )
      const edges = new DataSet(
        data.edges.map((e) => ({
          id: e.id,
          from: e.from,
          to: e.to,
          label: e.label,
        }))
      )

      const Network = vis.Network
      const network = new Network(containerRef.current, { nodes, edges }, {
        nodes: {
          shape: 'dot',
          size: 16,
          font: { size: 14, color: '#e0e0e0' },
          borderWidth: 2,
        },
        edges: {
          arrows: 'to',
          font: { size: 10, color: '#8888aa' },
          color: { color: '#2a2a4a', highlight: '#e94560' },
          smooth: { type: 'continuous' },
        },
        groups: {
          Project: { color: { background: '#e94560', border: '#d63851' } },
          Source: { color: { background: '#4a9eff', border: '#3a8eef' } },
          Entity: { color: { background: '#4ade80', border: '#3acf70' } },
          Claim: { color: { background: '#facc15', border: '#eabb14' } },
          Report: { color: { background: '#c084fc', border: '#b074ec' } },
        },
        physics: {
          solver: 'forceAtlas2Based',
        },
        interaction: {
          hover: true,
          tooltipDelay: 200,
        },
      })
      networkRef.current = network
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load graph')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (selectedProject) {
      void Promise.resolve().then(() => { loadGraph(selectedProject) })
    }
  }, [selectedProject, loadGraph])

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-white">Graph Viewer</h1>
        <select
          value={selectedProject}
          onChange={(e) => setSelectedProject(e.target.value)}
          className="bg-[#16213e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#e94560] transition-colors"
        >
          <option value="">Select project…</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
      </div>

      <Card className="flex-1 min-h-[500px] p-0 overflow-hidden" variant="surface">
        {!selectedProject ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-[#8888aa] text-sm p-8">
            <svg className="w-12 h-12 text-[#2a2a4a]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" />
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" /><line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
            </svg>
            <span>Select a project to visualize its knowledge graph</span>
          </div>
        ) : loading ? (
          <GraphSkeleton />
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 p-8">
            <svg className="w-10 h-10 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span className="text-red-400 text-sm">{error}</span>
            <button
              onClick={() => selectedProject && loadGraph(selectedProject)}
              className="text-xs text-[#8888aa] hover:text-white transition-colors underline"
            >
              Retry
            </button>
          </div>
        ) : (
          <div ref={containerRef} id="graph-container" className="w-full h-full" />
        )}
      </Card>
    </div>
  )
}
