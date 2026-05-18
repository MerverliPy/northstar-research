import type { ToolResult } from '../../types'
import { Badge } from '../shared/Badge'

interface ResultCardProps {
  result: ToolResult
}

function statusBadge(status: ToolResult['status']): 'green' | 'yellow' | 'red' | 'blue' {
  switch (status) {
    case 'completed': return 'green'
    case 'running': return 'blue'
    case 'failed': return 'red'
    default: return 'yellow'
  }
}

const toolMeta: Record<string, { label: string; color: string }> = {
  search: { label: 'Vector Search', color: 'border-l-blue-500' },
  extract: { label: 'LLM Extraction', color: 'border-l-purple-500' },
  quality_score: { label: 'Quality Scoring', color: 'border-l-green-500' },
  list_projects: { label: 'List Projects', color: 'border-l-cyan-500' },
  list_sources: { label: 'List Sources', color: 'border-l-cyan-500' },
  list_entities: { label: 'List Entities', color: 'border-l-cyan-500' },
  list_claims: { label: 'List Claims', color: 'border-l-cyan-500' },
  cleanup_report: { label: 'Cleanup Report', color: 'border-l-yellow-500' },
  cleanup_execute: { label: 'Execute Cleanup', color: 'border-l-yellow-500' },
  promote_import: { label: 'Promote Import', color: 'border-l-teal-500' },
  create_project: { label: 'Create Project', color: 'border-l-indigo-500' },
  create_source: { label: 'Create Source', color: 'border-l-indigo-500' },
}

function getToolMeta(tool: string) {
  return toolMeta[tool] || { label: tool, color: 'border-l-[#2a2a4a]' }
}

function renderData(_tool: string, data: unknown): string {
  if (typeof data === 'string') return data
  if (Array.isArray(data)) return `${data.length} items found`
  if (data && typeof data === 'object') {
    const obj = data as Record<string, unknown>
    if (obj.score !== undefined) return `Score: ${obj.score}`
    if (obj.total !== undefined) return `Total: ${obj.total}`
    return JSON.stringify(obj, null, 2).slice(0, 200)
  }
  return String(data)
}

export function ResultCard({ result }: ResultCardProps) {
  const meta = getToolMeta(result.tool)

  return (
    <div className={`mt-2 border border-[#2a2a4a] rounded-lg overflow-hidden bg-[#1a1a2e] border-l-2 ${meta.color}`}>
      <div className="flex items-center gap-2 px-3 py-2 bg-[#2a2a4a]/30 border-b border-[#2a2a4a]">
        <Badge variant={statusBadge(result.status)} dot>
          {result.status}
        </Badge>
        <span className="text-xs font-semibold text-white">{meta.label}</span>
        {result.type && (
          <span className="text-xs text-[#8888aa] ml-auto">{result.type}</span>
        )}
      </div>
      <div className="px-3 py-2 text-sm text-[#e0e0e0] font-mono whitespace-pre-wrap max-h-48 overflow-y-auto">
        {renderData(result.tool, result.data)}
      </div>
    </div>
  )
}
