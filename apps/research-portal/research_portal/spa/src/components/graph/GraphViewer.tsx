import { useEffect, useState, useRef } from 'react'
import { useProjectStore } from '../../stores/projectStore'
import { Card } from '../shared/Card'
import type { GraphData } from '../../types'

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

  const loadGraph = async (projectId: string) => {
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
  }

  useEffect(() => {
    if (selectedProject) {
      loadGraph(selectedProject)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProject])

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-white">Graph Viewer</h1>
        <select
          value={selectedProject}
          onChange={(e) => setSelectedProject(e.target.value)}
          className="bg-[#16213e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#e94560]"
        >
          <option value="">Select project…</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
      </div>

      <Card className="flex-1 min-h-[500px] p-0 overflow-hidden">
        {!selectedProject ? (
          <div className="flex items-center justify-center h-full text-[#8888aa] text-sm">
            Select a project to visualize its knowledge graph
          </div>
        ) : loading ? (
          <div className="flex items-center justify-center h-full text-[#8888aa] text-sm">
            Loading graph…
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-full text-red-400 text-sm">
            {error}
          </div>
        ) : (
          <div ref={containerRef} id="graph-container" className="w-full h-full" />
        )}
      </Card>
    </div>
  )
}
