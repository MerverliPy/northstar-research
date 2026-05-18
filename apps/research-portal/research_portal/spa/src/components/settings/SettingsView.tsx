import { useEffect } from 'react'
import { useSettingsStore } from '../../stores/settingsStore'
import { Card } from '../shared/Card'

function SectionIcon({ type }: { type: 'shield' | 'server' | 'info' }) {
  const cls = "w-4 h-4 text-[#e94560]"
  if (type === 'shield') {
    return (
      <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    )
  }
  if (type === 'server') {
    return (
      <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="2" width="20" height="8" rx="2" ry="2" /><rect x="2" y="14" width="20" height="8" rx="2" ry="2" /><line x1="6" y1="6" x2="6.01" y2="6" /><line x1="6" y1="18" x2="6.01" y2="18" />
      </svg>
    )
  }
  return (
    <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
  )
}

export function SettingsView() {
  const { settings, fetchSettings } = useSettingsStore()

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6">
      <h1 className="text-xl font-bold text-white mb-6">Settings</h1>

      <div className="space-y-4 max-w-2xl">
        <Card variant="surface">
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <SectionIcon type="shield" />
            Safety Gates
          </h2>

          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-[#2a2a4a]/50">
              <div>
                <div className="text-sm font-medium text-white">Force Graph Extraction</div>
                <div className="text-xs text-[#8888aa] mt-0.5">
                  Enables entity/claim extraction via LLM. Set <code className="text-[#e0e0e0]">FORCE_GRAPH_EXTRACTION=true</code> in environment.
                </div>
              </div>
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
                settings.force_graph_extraction
                  ? 'bg-green-900/40 text-green-300 border border-green-700'
                  : 'bg-red-900/40 text-red-300 border border-red-700'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${
                  settings.force_graph_extraction ? 'bg-green-400' : 'bg-red-400'
                }`} />
                {settings.force_graph_extraction ? 'ENABLED' : 'DISABLED'}
              </span>
            </div>

            <div className="flex items-center justify-between py-3">
              <div>
                <div className="text-sm font-medium text-white">Destructive Cleanup</div>
                <div className="text-xs text-[#8888aa] mt-0.5">
                  Allows deletion of orphaned entities. Set <code className="text-[#e0e0e0]">ENABLE_DESTRUCTIVE_CLEANUP=true</code> in environment.
                </div>
              </div>
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
                settings.enable_destructive_cleanup
                  ? 'bg-green-900/40 text-green-300 border border-green-700'
                  : 'bg-red-900/40 text-red-300 border border-red-700'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${
                  settings.enable_destructive_cleanup ? 'bg-green-400' : 'bg-red-400'
                }`} />
                {settings.enable_destructive_cleanup ? 'ENABLED' : 'DISABLED'}
              </span>
            </div>
          </div>
        </Card>

        <Card variant="surface">
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <SectionIcon type="server" />
            Service Endpoints
          </h2>

          <div className="space-y-3">
            <div className="py-2 border-b border-[#2a2a4a]/50">
              <div className="text-xs text-[#8888aa]">Research Agent</div>
              <div className="text-sm text-white font-mono">{settings.research_agent_url}</div>
            </div>
            <div className="py-2 border-b border-[#2a2a4a]/50">
              <div className="text-xs text-[#8888aa]">Chat Import Bridge</div>
              <div className="text-sm text-white font-mono">{settings.chat_import_bridge_url}</div>
            </div>
            <div className="py-2">
              <div className="text-xs text-[#8888aa]">Log Level</div>
              <div className="text-sm text-white font-mono">{settings.log_level}</div>
            </div>
          </div>
        </Card>

        <Card variant="surface">
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <SectionIcon type="info" />
            About
          </h2>
          <div className="space-y-2 text-sm text-[#8888aa]">
            <p>Northstar Research Console v0.2.0</p>
            <p>PWA interface for AI-powered research with PostgreSQL, Neo4j, and Ollama.</p>
            <p className="text-xs mt-4">
              Safety gates are read-only in the UI. To toggle them, set the environment variables
              and restart the portal service.
            </p>
          </div>
        </Card>
      </div>
    </div>
  )
}
