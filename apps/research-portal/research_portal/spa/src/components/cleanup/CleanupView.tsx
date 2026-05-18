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
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
        <div className="flex items-start gap-3 bg-yellow-900/20 border border-yellow-700/50 text-yellow-300 text-sm rounded-lg px-4 py-3 mb-4">
          <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          <div>
            <p className="font-medium mb-0.5">Destructive cleanup is disabled</p>
            <p className="text-yellow-300/70 text-xs">
              Set <code className="text-yellow-300">ENABLE_DESTRUCTIVE_CLEANUP=true</code> in the portal environment to enable.
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card variant="surface" hover>
          <div className="text-xs uppercase tracking-wider text-[#8888aa] mb-1">Orphaned Entities</div>
          {loading && !report ? (
            <div className="skeleton h-8 w-12 mt-1" />
          ) : (
            <div className="text-3xl font-bold text-red-400">{report?.total_orphaned ?? '-'}</div>
          )}
        </Card>
        <Card variant="surface" hover>
          <div className="text-xs uppercase tracking-wider text-[#8888aa] mb-1">Cleanup Enabled</div>
          <div className="mt-1">
            <Badge variant={settings.enable_destructive_cleanup ? 'green' : 'red'}>
              {settings.enable_destructive_cleanup ? 'Yes' : 'No'}
            </Badge>
          </div>
        </Card>
        <Card variant="surface" hover>
          <div className="text-xs uppercase tracking-wider text-[#8888aa] mb-1">Status</div>
          <div className="text-lg font-bold">
            {loading && !report ? (
              <div className="skeleton h-7 w-16 mt-0.5" />
            ) : error ? (
              <span className="text-red-400">Error</span>
            ) : report ? (
              <span className="text-green-400">Ready</span>
            ) : (
              <span className="text-[#8888aa]">Unknown</span>
            )}
          </div>
        </Card>
      </div>

      {error && (
        <div className="flex items-center gap-3 bg-red-900/20 border border-red-700/50 text-red-300 text-sm rounded-lg px-4 py-3 mb-4">
          <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className="relative bg-green-900/20 border border-green-700/50 text-green-300 text-sm rounded-lg px-4 py-3 mb-4 font-mono whitespace-pre-wrap max-h-40 overflow-y-auto">
          <button
            onClick={() => setResult(null)}
            className="absolute top-2 right-2 text-[#8888aa] hover:text-white text-xs transition-colors"
          >
            Dismiss
          </button>
          {result}
        </div>
      )}

      <div className="flex gap-3 mb-6">
        <Button variant="secondary" onClick={fetchReport} loading={loading}>
          Refresh Report
        </Button>
        <Button
          variant="danger"
          onClick={executeCleanup}
          disabled={!settings.enable_destructive_cleanup || executing || (report?.total_orphaned ?? 0) === 0}
          loading={executing}
        >
          Execute Cleanup
        </Button>
      </div>

      {report && (
        <Card variant="surface">
          <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <svg className="w-4 h-4 text-[#8888aa]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            Orphaned Entities
          </h2>
          {report.suggestions.length > 0 && (
            <div className="mb-4 p-3 bg-blue-900/20 border border-blue-700/50 rounded-lg">
              <div className="text-xs text-blue-300 font-medium mb-1">Suggestions</div>
              {report.suggestions.map((s, i) => (
                <div key={i} className="text-xs text-blue-200/80 mt-1">{s}</div>
              ))}
            </div>
          )}
          {report.orphaned_entities.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-8">
              <svg className="w-10 h-10 text-green-400/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm text-[#8888aa]">No orphaned entities found</p>
            </div>
          ) : (
            <div className="space-y-2">
              {report.orphaned_entities.map((entity: Entity) => (
                <div key={entity.id} className="flex items-center justify-between py-2 px-3 bg-[#1a1a2e] rounded-md hover:bg-[#1a1a2e]/80 transition-colors">
                  <div>
                    <span className="text-sm text-white">{entity.name}</span>
                    <span className="text-xs text-[#8888aa] ml-2">({entity.entity_type})</span>
                  </div>
                  <span className="text-xs text-[#8888aa] font-mono">{entity.id.slice(0, 8)}...</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
