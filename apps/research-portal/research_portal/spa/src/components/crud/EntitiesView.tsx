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
import type { Entity } from '../../types'

interface EntityForm {
  name: string
  entity_type: string
  description: string
  project_id: string
  source_id: string
}

export function EntitiesView() {
  const {
    entities, projects, entitiesTotal, entitiesPage, entitiesPageSize,
    fetchEntities, createEntity, deleteEntity, fetchProjects,
  } = useProjectStore()
  const addToast = useToastStore((s) => s.addToast)
  const [modalOpen, setModalOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [filterProject, setFilterProject] = useState('')
  const { form, errors, setField, validateAll, resetForm } = useForm<EntityForm>(
    { name: '', entity_type: 'person', description: '', project_id: '', source_id: '' },
    { name: required('Entity name is required') }
  )

  useEffect(() => {
    fetchProjects()
    fetchEntities()
  }, [fetchProjects, fetchEntities])

  useEffect(() => {
    fetchEntities(filterProject ? { project_id: filterProject } : undefined)
  }, [filterProject, fetchEntities])

  const handleSubmit = async () => {
    if (!validateAll()) return
    setSubmitting(true)
    try {
      await createEntity({
        name: form.name,
        entity_type: form.entity_type,
        description: form.description || null,
        project_id: form.project_id || null,
        source_id: form.source_id || null,
      } as Partial<Entity>)
      addToast('Entity created', 'success')
      setModalOpen(false)
      resetForm({ name: '', entity_type: 'person', description: '', project_id: '', source_id: '' })
    } catch {
      addToast('Failed to create entity', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const columns = [
    { key: 'name', header: 'Name', render: (e: Entity) => <span className="text-white font-medium">{e.name}</span> },
    { key: 'entity_type', header: 'Type', render: (e: Entity) => <Badge variant="green">{e.entity_type}</Badge> },
    { key: 'description', header: 'Description', render: (e: Entity) => e.description ? <span className="text-xs text-[#8888aa] line-clamp-1">{e.description.slice(0, 80)}</span> : <span className="text-xs text-[#8888aa]">-</span> },
    { key: 'created_at', header: 'Created', render: (e: Entity) => new Date(e.created_at).toLocaleDateString() },
    { key: 'id', header: '', render: (e: Entity) => (
      <Button variant="danger" size="sm" onClick={async (ev) => { ev.stopPropagation(); try { await deleteEntity(e.id); addToast('Entity deleted', 'success') } catch { addToast('Failed to delete entity', 'error') } }}>Delete</Button>
    )},
  ]

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-white">Entities</h1>
        <div className="flex gap-3">
          <select
            value={filterProject}
            onChange={(e) => setFilterProject(e.target.value)}
            className="bg-[#16213e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#e94560] transition-colors"
          >
            <option value="">All projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <Button onClick={() => setModalOpen(true)}>+ New Entity</Button>
        </div>
      </div>

      <Card variant="surface">
        <Table columns={columns} data={entities} keyField="id" emptyMessage="No entities yet" />
        <Pagination
          currentPage={entitiesPage}
          totalPages={Math.max(1, Math.ceil(entitiesTotal / entitiesPageSize))}
          total={entitiesTotal}
          pageSize={entitiesPageSize}
          onPageChange={(p) => fetchEntities(filterProject ? { project_id: filterProject } : undefined, p)}
          onPageSizeChange={(size) => fetchEntities(filterProject ? { project_id: filterProject } : undefined, 1, size)}
        />
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Entity">
        <form className="space-y-4" noValidate onSubmit={(e) => { e.preventDefault(); handleSubmit() }}>
          <div>
            <label htmlFor="entity-name" className="block text-sm text-[#8888aa] mb-1">Name</label>
            <input
              id="entity-name"
              value={form.name}
              onChange={(e) => setField('name', e.target.value)}
              className={`w-full bg-[#1a1a2e] border rounded-md px-3 py-2 text-sm text-white placeholder-[#8888aa] focus:outline-none focus:border-[#e94560] transition-colors ${errors.name ? 'border-red-500' : 'border-[#2a2a4a]'}`}
              placeholder="Entity name"
              aria-invalid={!!errors.name}
              aria-describedby={errors.name ? 'entity-name-error' : undefined}
            />
            {errors.name && (
              <span id="entity-name-error" className="block text-xs text-red-400 mt-1">{errors.name}</span>
            )}
          </div>
          <div>
            <label htmlFor="entity-type" className="block text-sm text-[#8888aa] mb-1">Type</label>
            <select
              id="entity-type"
              value={form.entity_type}
              onChange={(e) => setField('entity_type', e.target.value)}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#e94560] transition-colors"
            >
              <option value="person">Person</option>
              <option value="organization">Organization</option>
              <option value="location">Location</option>
              <option value="concept">Concept</option>
              <option value="event">Event</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label htmlFor="entity-desc" className="block text-sm text-[#8888aa] mb-1">Description</label>
            <textarea
              id="entity-desc"
              value={form.description}
              onChange={(e) => setField('description', e.target.value)}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white placeholder-[#8888aa] focus:outline-none focus:border-[#e94560] transition-colors resize-none"
              rows={2}
              placeholder="Optional"
            />
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
