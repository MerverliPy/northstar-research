import { useEffect } from 'react'
import { useSettingsStore } from '../../stores/settingsStore'
import { Card } from '../shared/Card'
import { Badge } from '../shared/Badge'

export function SettingsView() {
  const { settings, fetchSettings } = useSettingsStore()

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6">
      <h1 className="text-xl font-bold text-white mb-6">Settings</h1>

      <div className="space-y-4 max-w-2xl">
        <Card>
          <h2 className="text-sm font-semibold text-white mb-4">Safety Gates</h2>

          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-[#2a2a4a]/50">
              <div>
                <div className="text-sm font-medium text-white">Force Graph Extraction</div>
                <div className="text-xs text-[#8888aa] mt-0.5">
                  Enables entity/claim extraction via LLM. Set FORCE_GRAPH_EXTRACTION=true in environment.
                </div>
              </div>
              <Badge variant={settings.force_graph_extraction ? 'green' : 'red'}>
                {settings.force_graph_extraction ? 'ENABLED' : 'DISABLED'}
              </Badge>
            </div>

            <div className="flex items-center justify-between py-3">
              <div>
                <div className="text-sm font-medium text-white">Destructive Cleanup</div>
                <div className="text-xs text-[#8888aa] mt-0.5">
                  Allows deletion of orphaned entities. Set ENABLE_DESTRUCTIVE_CLEANUP=true in environment.
                </div>
              </div>
              <Badge variant={settings.enable_destructive_cleanup ? 'green' : 'red'}>
                {settings.enable_destructive_cleanup ? 'ENABLED' : 'DISABLED'}
              </Badge>
            </div>
          </div>
        </Card>

        <Card>
          <h2 className="text-sm font-semibold text-white mb-4">Service Endpoints</h2>

          <div className="space-y-3">
            <div className="py-2 border-b border-[#2a2a4a]/50">
              <div className="text-xs text-[#8888aa]">Research Agent</div>
              <div className="text-sm text-white">{settings.research_agent_url}</div>
            </div>
            <div className="py-2 border-b border-[#2a2a4a]/50">
              <div className="text-xs text-[#8888aa]">Chat Import Bridge</div>
              <div className="text-sm text-white">{settings.chat_import_bridge_url}</div>
            </div>
            <div className="py-2">
              <div className="text-xs text-[#8888aa]">Log Level</div>
              <div className="text-sm text-white">{settings.log_level}</div>
            </div>
          </div>
        </Card>

        <Card>
          <h2 className="text-sm font-semibold text-white mb-4">About</h2>
          <div className="space-y-2 text-sm text-[#8888aa]">
            <p>Northstar Research Console v0.1.0</p>
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
