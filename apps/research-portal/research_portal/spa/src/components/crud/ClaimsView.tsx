import { useEffect, useState } from 'react'
import { useProjectStore } from '../../stores/projectStore'
import { useToastStore } from '../../stores/toastStore'
import { useForm, required } from '../../hooks/useForm'
import { Card } from '../shared/Card'
import { Button } from '../shared/Button'
import { Modal } from '../shared/Modal'
import { Table } from '../shared/Table'
import { Pagination } from '../shared/Pagination'
import { Badge } from '../shared/Badge'
import type { Claim } from '../../types'

interface ClaimForm {
  content: string
  confidence: number
  source_id: string
  entity_id: string
}

export function ClaimsView() {
  const {
    claims, claimsTotal, claimsPage, claimsPageSize,
    fetchClaims, createClaim, deleteClaim,
  } = useProjectStore()
  const addToast = useToastStore((s) => s.addToast)
  const [modalOpen, setModalOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const { form, errors, setField, validateAll, resetForm } = useForm<ClaimForm>(
    { content: '', confidence: 0.5, source_id: '', entity_id: '' },
    { content: required('Claim content is required') }
  )

  useEffect(() => {
    fetchClaims()
  }, [fetchClaims])

  const handleSubmit = async () => {
    if (!validateAll()) return
    setSubmitting(true)
    try {
      await createClaim({
        content: form.content,
        confidence: form.confidence,
        source_id: form.source_id || null,
        entity_id: form.entity_id || null,
      } as Partial<Claim>)
      addToast('Claim created', 'success')
      setModalOpen(false)
      resetForm({ content: '', confidence: 0.5, source_id: '', entity_id: '' })
    } catch {
      addToast('Failed to create claim', 'error')
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
      <Button variant="danger" size="sm" onClick={async (e) => { e.stopPropagation(); try { await deleteClaim(c.id); addToast('Claim deleted', 'success') } catch { addToast('Failed to delete claim', 'error') } }}>Delete</Button>
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
        <Pagination
          currentPage={claimsPage}
          totalPages={Math.max(1, Math.ceil(claimsTotal / claimsPageSize))}
          total={claimsTotal}
          pageSize={claimsPageSize}
          onPageChange={(p) => fetchClaims(undefined, p)}
          onPageSizeChange={(size) => fetchClaims(undefined, 1, size)}
        />
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Claim">
        <form className="space-y-4" noValidate onSubmit={(e) => { e.preventDefault(); handleSubmit() }}>
          <div>
            <label htmlFor="claim-content" className="block text-sm text-[#8888aa] mb-1">Content</label>
            <textarea
              id="claim-content"
              value={form.content}
              onChange={(e) => setField('content', e.target.value)}
              className={`w-full bg-[#1a1a2e] border rounded-md px-3 py-2 text-sm text-white placeholder-[#8888aa] focus:outline-none focus:border-[#e94560] transition-colors resize-none ${errors.content ? 'border-red-500' : 'border-[#2a2a4a]'}`}
              rows={3}
              placeholder="Claim statement…"
              aria-invalid={!!errors.content}
              aria-describedby={errors.content ? 'claim-content-error' : undefined}
            />
            {errors.content && (
              <span id="claim-content-error" className="block text-xs text-red-400 mt-1">{errors.content}</span>
            )}
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
                onChange={(e) => setField('confidence', parseFloat(e.target.value))}
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
            <Button type="submit" loading={submitting}>Create</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
