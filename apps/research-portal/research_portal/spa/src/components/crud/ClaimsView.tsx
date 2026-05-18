import { useEffect, useState } from 'react'
import { useProjectStore } from '../../stores/projectStore'
import { Card } from '../shared/Card'
import { Button } from '../shared/Button'
import { Modal } from '../shared/Modal'
import { Table } from '../shared/Table'
import { Badge } from '../shared/Badge'
import type { Claim } from '../../types'

export function ClaimsView() {
  const { claims, fetchClaims, createClaim, deleteClaim } = useProjectStore()
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState({ content: '', confidence: 0.5, source_id: '', entity_id: '' })

  useEffect(() => {
    fetchClaims()
  }, [fetchClaims])

  const handleSubmit = async () => {
    if (!form.content.trim()) return
    await createClaim({
      content: form.content,
      confidence: form.confidence,
      source_id: form.source_id || null,
      entity_id: form.entity_id || null,
    } as Partial<Claim>)
    setModalOpen(false)
    setForm({ content: '', confidence: 0.5, source_id: '', entity_id: '' })
  }

  const confidenceBadge = (c: number | null): 'green' | 'yellow' | 'red' | 'gray' => {
    if (c === null) return 'gray'
    if (c >= 0.7) return 'green'
    if (c >= 0.4) return 'yellow'
    return 'red'
  }

  const columns = [
    { key: 'content', header: 'Claim', render: (c: Claim) => <span className="text-white text-sm line-clamp-2">{c.content}</span> },
    { key: 'confidence', header: 'Confidence', render: (c: Claim) => <Badge variant={confidenceBadge(c.confidence)}>{c.confidence?.toFixed(2) ?? 'N/A'}</Badge> },
    { key: 'created_at', header: 'Created', render: (c: Claim) => new Date(c.created_at).toLocaleDateString() },
    { key: 'id', header: '', render: (c: Claim) => (
      <Button variant="danger" size="sm" onClick={(e) => { e.stopPropagation(); deleteClaim(c.id) }}>Delete</Button>
    )},
  ]

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-white">Claims</h1>
        <Button onClick={() => setModalOpen(true)}>+ New Claim</Button>
      </div>

      <Card>
        <Table columns={columns} data={claims} keyField="id" emptyMessage="No claims yet" />
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Claim">
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-[#8888aa] mb-1">Content</label>
            <textarea
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#e94560] resize-none"
              rows={3}
              placeholder="Claim statement…"
            />
          </div>
          <div>
            <label className="block text-sm text-[#8888aa] mb-1">Confidence ({form.confidence.toFixed(2)})</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={form.confidence}
              onChange={(e) => setForm({ ...form, confidence: parseFloat(e.target.value) })}
              className="w-full accent-[#e94560]"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={!form.content.trim()}>Create</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
