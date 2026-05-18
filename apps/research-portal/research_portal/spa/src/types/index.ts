export interface Project {
  id: string
  name: string
  description: string | null
  metadata: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface Source {
  id: string
  project_id: string
  title: string
  content: string
  source_type: string
  metadata: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface Entity {
  id: string
  source_id: string | null
  project_id: string | null
  name: string
  entity_type: string
  description: string | null
  metadata: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface Claim {
  id: string
  source_id: string | null
  entity_id: string | null
  content: string
  confidence: number | null
  metadata: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface Report {
  id: string
  project_id: string
  title: string
  content: string
  report_type: string
  metadata: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface StagedImport {
  id: string
  title: string
  content: string
  source_type: string
  status: 'pending' | 'promoted' | 'failed'
  created_at: string
  updated_at: string
}

export interface ExtractionJob {
  extraction_id: string
  source_id: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  created_at: string
}

export interface QualityScore {
  source_id: string
  score: number
  reasoning: string
  quality_status: string
  created_at: string
}

export interface GraphData {
  nodes: Array<{
    id: string
    label: string
    group: string
    title?: string
  }>
  edges: Array<{
    id: string
    from: string
    to: string
    label: string
  }>
}

export interface CleanupReport {
  orphaned_entities: Entity[]
  total_orphaned: number
  suggestions: string[]
}

export interface DashboardStats {
  projects: number
  sources: number
  entities: number
  claims: number
  reports: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export interface ChatMessage {
  id: string
  conversation_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  tool_results?: ToolResult[]
  created_at: string
}

export interface ToolResult {
  tool: string
  type: string
  status: 'running' | 'completed' | 'failed'
  data: unknown
}

export interface Conversation {
  id: string
  title: string
  project_id: string | null
  created_at: string
  updated_at: string
}

export interface SSEEvent {
  event: 'thinking' | 'action' | 'result' | 'done' | 'error'
  data: Record<string, unknown>
}

export interface Settings {
  force_graph_extraction: boolean
  enable_destructive_cleanup: boolean
  research_agent_url: string
  chat_import_bridge_url: string
  log_level: string
}
