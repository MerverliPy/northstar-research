import { useEffect, useState } from 'react'
import { Card } from '../shared/Card'
import { Button } from '../shared/Button'
import { Badge } from '../shared/Badge'
import { useSettingsStore } from '../../stores/settingsStore'
import type { CleanupReport, Entity } from '../../types'

export function CleanupView() {
  const { settings, fetchSettings } = useSettingsStore()
  const [report, setReport] = useState<CleanupReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<string | null>(null)

  useEffect(() => {
    fetchSettings()
    fetchReport()
  }, [fetchSettings])

  const fetchReport = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/v1/cleanup/report')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setReport(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load report')
    } finally {
      setLoading(false)
    }
  }

  const executeCleanup = async () => {
    if (!settings.enable_destructive_cleanup) return
    setExecuting(true)
    setResult(null)
    try {
      const res = await fetch('/api/v1/cleanup/execute', { method: 'POST' })
      if (!res.ok) {
        const err = await res.text()
        throw new Error(err)
      }
      const data = await res.json()
      setResult(JSON.stringify(data, null, 2))
      await fetchReport()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Cleanup failed')
    } finally {
      setExecuting(false)
    }
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6">
      <h1 className="text-xl font-bold text-white mb-6">Cleanup</h1>

      {!settings.enable_destructive_cleanup && (
        <div className="bg-yellow-900/20 border border-yellow-700 text-yellow-300 text-sm rounded-lg px-4 py-3 mb-4">
          Destructive cleanup is disabled. Set <code>ENABLE_DESTRUCTIVE_CLEANUP=true</code> to enable.
        </div>
      )}

      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card>
          <div className="text-xs uppercase tracking-wider text-[#8888aa] mb-1">Orphaned Entities</div>
          <div className="text-3xl font-bold text-red-400">{report?.total_orphaned ?? '-'}</div>
        </Card>
        <Card>
          <div className="text-xs uppercase tracking-wider text-[#8888aa] mb-1">Cleanup Enabled</div>
          <Badge variant={settings.enable_destructive_cleanup ? 'green' : 'red'}>
            {settings.enable_destructive_cleanup ? 'Yes' : 'No'}
          </Badge>
        </Card>
        <Card>
          <div className="text-xs uppercase tracking-wider text-[#8888aa] mb-1">Status</div>
          <div className="text-lg font-bold text-white">
            {loading ? 'Loading…' : error ? 'Error' : report ? 'Ready' : 'Unknown'}
          </div>
        </Card>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-700 text-red-300 text-sm rounded-lg px-4 py-3 mb-4">
          {error}
        </div>
      )}

      {result && (
        <div className="bg-green-900/20 border border-green-700 text-green-300 text-sm rounded-lg px-4 py-3 mb-4 font-mono whitespace-pre-wrap">
          {result}
        </div>
      )}

      <div className="flex gap-3 mb-6">
        <Button variant="secondary" onClick={fetchReport} disabled={loading}>
          Refresh Report
        </Button>
        <Button
          variant="danger"
          onClick={executeCleanup}
          disabled={!settings.enable_destructive_cleanup || executing || (report?.total_orphaned ?? 0) === 0}
        >
          {executing ? 'Executing…' : 'Execute Cleanup'}
        </Button>
      </div>

      {report && (
        <Card>
          <h2 className="text-sm font-semibold text-white mb-3">Orphaned Entities</h2>
          {report.suggestions.length > 0 && (
            <div className="mb-4 p-3 bg-blue-900/20 border border-blue-700 rounded-lg">
              <div className="text-xs text-blue-300 font-medium mb-1">Suggestions</div>
              {report.suggestions.map((s, i) => (
                <div key={i} className="text-xs text-blue-200">{s}</div>
              ))}
            </div>
          )}
          {report.orphaned_entities.length === 0 ? (
            <p className="text-[#8888aa] text-sm py-4 text-center">No orphaned entities found</p>
          ) : (
            <div className="space-y-2">
              {report.orphaned_entities.map((entity: Entity) => (
                <div key={entity.id} className="flex items-center justify-between py-2 px-3 bg-[#1a1a2e] rounded-md">
                  <div>
                    <span className="text-sm text-white">{entity.name}</span>
                    <span className="text-xs text-[#8888aa] ml-2">({entity.entity_type})</span>
                  </div>
                  <span className="text-xs text-[#8888aa]">{entity.id.slice(0, 8)}…</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
