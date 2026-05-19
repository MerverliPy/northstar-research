import { useEffect, useState, useCallback } from 'react'
import { Card } from '../shared/Card'
import { Button } from '../shared/Button'
import { Badge } from '../shared/Badge'
import { Table } from '../shared/Table'
import { Modal } from '../shared/Modal'
import type { StagedImport } from '../../types'

const BRIDGE_URL = '/api/v1/import'

export function ImportView() {
  const [imports, setImports] = useState<StagedImport[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState({ title: '', content: '', source_type: 'paste' })
  const [promoting, setPromoting] = useState<string | null>(null)
  const [batchPromoting, setBatchPromoting] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const fetchImports = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${BRIDGE_URL}s/?limit=100`)
      if (res.ok) {
        const data = await res.json()
        setImports(data.items || data)
      }
    } catch {
      // bridge may not be running
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void Promise.resolve().then(() => { fetchImports() })
  }, [fetchImports])

  const handlePaste = async () => {
    if (!form.content.trim()) return
    try {
      const res = await fetch(`${BRIDGE_URL}s/paste`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      if (res.ok) {
        setModalOpen(false)
        setForm({ title: '', content: '', source_type: 'paste' })
        await fetchImports()
      }
    } catch {
      // ignore
    }
  }

  const promoteOne = async (id: string) => {
    setPromoting(id)
    try {
      const res = await fetch(`/api/v1/promotion/${id}`, { method: 'POST' })
      const data = await res.json()
      setResult(`Promoted: ${JSON.stringify(data)}`)
      await fetchImports()
    } catch (e) {
      setResult(`Error: ${e}`)
    } finally {
      setPromoting(null)
    }
  }

  const promoteAll = async () => {
    setBatchPromoting(true)
    try {
      const res = await fetch('/api/v1/promotion/batch', { method: 'POST' })
      const data = await res.json()
      setResult(JSON.stringify(data, null, 2))
      await fetchImports()
    } catch (e) {
      setResult(`Error: ${e}`)
    } finally {
      setBatchPromoting(false)
    }
  }

  const deleteImport = async (id: string) => {
    await fetch(`${BRIDGE_URL}s/${id}`, { method: 'DELETE' })
    await fetchImports()
  }

  const columns = [
    { key: 'title', header: 'Title', render: (i: StagedImport) => <span className="text-white font-medium">{i.title}</span> },
    { key: 'source_type', header: 'Type', render: (i: StagedImport) => <Badge variant="blue">{i.source_type}</Badge> },
    { key: 'status', header: 'Status', render: (i: StagedImport) => {
      const v = i.status === 'promoted' ? 'green' : i.status === 'failed' ? 'red' : 'yellow'
      return <Badge variant={v}>{i.status}</Badge>
    }},
    { key: 'created_at', header: 'Created', render: (i: StagedImport) => new Date(i.created_at).toLocaleDateString() },
    { key: 'id', header: '', render: (i: StagedImport) => (
      <div className="flex gap-2">
        {i.status === 'pending' && (
          <Button variant="primary" size="sm" onClick={(e) => { e.stopPropagation(); promoteOne(i.id) }} loading={promoting === i.id}>
            Promote
          </Button>
        )}
        <Button variant="danger" size="sm" onClick={(e) => { e.stopPropagation(); deleteImport(i.id) }}>Delete</Button>
      </div>
    )},
  ]

  const pendingCount = imports.filter((i) => i.status === 'pending').length

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-white">Chat Import Bridge</h1>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={() => setModalOpen(true)}>+ Paste Import</Button>
          <Button onClick={promoteAll} disabled={batchPromoting || pendingCount === 0} loading={batchPromoting}>
            Promote All ({pendingCount})
          </Button>
        </div>
      </div>

      {result && (
        <div className="relative bg-green-900/20 border border-green-700/50 text-green-300 text-sm rounded-lg px-4 py-3 mb-4 font-mono whitespace-pre-wrap max-h-40 overflow-y-auto animate-pulse">
          <button
            onClick={() => setResult(null)}
            className="absolute top-2 right-2 text-xs text-[#8888aa] hover:text-white transition-colors"
          >
            Dismiss
          </button>
          {result}
        </div>
      )}

      <Card variant="surface">
        {loading && imports.length === 0 ? (
          <div className="space-y-3 p-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex gap-4">
                <div className="skeleton h-4 flex-1" />
                <div className="skeleton h-4 w-16" />
                <div className="skeleton h-4 w-20" />
                <div className="skeleton h-4 w-24" />
                <div className="skeleton h-4 w-28" />
              </div>
            ))}
          </div>
        ) : (
          <Table columns={columns} data={imports} keyField="id" emptyMessage="No staged imports. Paste a chat transcript to get started." />
        )}
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Paste Chat Import">
        <div className="space-y-4">
          <div>
            <label htmlFor="import-title" className="block text-sm text-[#8888aa] mb-1">Title</label>
            <input
              id="import-title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white placeholder-[#8888aa] focus:outline-none focus:border-[#e94560] transition-colors"
              placeholder="Import title"
            />
          </div>
          <div>
            <label htmlFor="import-content" className="block text-sm text-[#8888aa] mb-1">Content</label>
            <textarea
              id="import-content"
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white placeholder-[#8888aa] focus:outline-none focus:border-[#e94560] transition-colors resize-none"
              rows={6}
              placeholder="Paste chat transcript..."
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button onClick={handlePaste} disabled={!form.content.trim()}>Import</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
