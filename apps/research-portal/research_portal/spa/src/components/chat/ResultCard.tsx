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

function formatToolLabel(tool: string): string {
  const labels: Record<string, string> = {
    search: 'Vector Search',
    extract: 'LLM Extraction',
    quality_score: 'Quality Scoring',
    list_projects: 'List Projects',
    list_sources: 'List Sources',
    list_entities: 'List Entities',
    list_claims: 'List Claims',
    cleanup_report: 'Cleanup Report',
    cleanup_execute: 'Execute Cleanup',
    promote_import: 'Promote Import',
    create_project: 'Create Project',
    create_source: 'Create Source',
  }
  return labels[tool] || tool
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
  return (
    <div className="mt-2 border border-[#2a2a4a] rounded-lg overflow-hidden bg-[#1a1a2e]">
      <div className="flex items-center gap-2 px-3 py-2 bg-[#2a2a4a]/50 border-b border-[#2a2a4a]">
        <span className="text-xs font-semibold text-white">{formatToolLabel(result.tool)}</span>
        <Badge variant={statusBadge(result.status)}>{result.status}</Badge>
        {result.type && (
          <span className="text-xs text-[#8888aa]">{result.type}</span>
        )}
      </div>
      <div className="px-3 py-2 text-sm text-[#e0e0e0] font-mono whitespace-pre-wrap max-h-48 overflow-y-auto">
        {renderData(result.tool, result.data)}
      </div>
    </div>
  )
}
