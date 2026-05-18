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
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState({ content: '', confidence: 0.5, source_id: '', entity_id: '' })

  useEffect(() => {
    fetchClaims()
  }, [fetchClaims])

  const handleSubmit = async () => {
    if (!form.content.trim()) return
    setSubmitting(true)
    try {
      await createClaim({
        content: form.content,
        confidence: form.confidence,
        source_id: form.source_id || null,
        entity_id: form.entity_id || null,
      } as Partial<Claim>)
      setModalOpen(false)
      setForm({ content: '', confidence: 0.5, source_id: '', entity_id: '' })
    } finally {
      setSubmitting(false)
    }
  }

  const confidenceBadge = (c: number | null): 'green' | 'yellow' | 'red' | 'gray' => {
    if (c === null) return 'gray'
    if (c >= 0.7) return 'green'
    if (c >= 0.4) return 'yellow'
    return 'red'
  }

  const confidencePercent = (c: number | null): string => {
    if (c === null) return 'N/A'
    return `${Math.round(c * 100)}%`
  }

  const columns = [
    { key: 'content', header: 'Claim', render: (c: Claim) => <span className="text-white text-sm line-clamp-2">{c.content}</span> },
    { key: 'confidence', header: 'Confidence', render: (c: Claim) => <Badge variant={confidenceBadge(c.confidence)}>{confidencePercent(c.confidence)}</Badge> },
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

      <Card variant="surface">
        <Table columns={columns} data={claims} keyField="id" emptyMessage="No claims yet" />
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Claim">
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-[#8888aa] mb-1">Content</label>
            <textarea
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white placeholder-[#8888aa] focus:outline-none focus:border-[#e94560] transition-colors resize-none"
              rows={3}
              placeholder="Claim statement…"
            />
          </div>
          <div>
            <label className="block text-sm text-[#8888aa] mb-2">
              Confidence: <span className="text-white font-medium">{Math.round(form.confidence * 100)}%</span>
            </label>
            <div className="relative h-2 bg-[#2a2a4a] rounded-full overflow-hidden">
              <div
                className="absolute inset-y-0 left-0 rounded-full transition-all duration-200"
                style={{
                  width: `${form.confidence * 100}%`,
                  background: form.confidence < 0.4
                    ? '#ef4444'
                    : form.confidence < 0.7
                      ? '#eab308'
                      : '#22c55e',
                }}
              />
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={form.confidence}
                onChange={(e) => setForm({ ...form, confidence: parseFloat(e.target.value) })}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
            </div>
            <div className="flex justify-between text-[10px] text-[#8888aa] mt-1">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={!form.content.trim()} loading={submitting}>Create</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
