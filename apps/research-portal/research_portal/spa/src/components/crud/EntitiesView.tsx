import { useEffect, useState } from 'react'
import { useProjectStore } from '../../stores/projectStore'
import { Card } from '../shared/Card'
import { Button } from '../shared/Button'
import { Modal } from '../shared/Modal'
import { Table } from '../shared/Table'
import { Badge } from '../shared/Badge'
import type { Entity } from '../../types'

export function EntitiesView() {
  const { entities, projects, fetchEntities, createEntity, deleteEntity, fetchProjects } = useProjectStore()
  const [modalOpen, setModalOpen] = useState(false)
  const [filterProject, setFilterProject] = useState('')
  const [form, setForm] = useState({ name: '', entity_type: 'person', description: '', project_id: '', source_id: '' })

  useEffect(() => {
    fetchProjects()
    fetchEntities()
  }, [fetchProjects, fetchEntities])

  useEffect(() => {
    fetchEntities(filterProject ? { project_id: filterProject } : undefined)
  }, [filterProject, fetchEntities])

  const handleSubmit = async () => {
    if (!form.name.trim()) return
    await createEntity({
      name: form.name,
      entity_type: form.entity_type,
      description: form.description || null,
      project_id: form.project_id || null,
      source_id: form.source_id || null,
    } as Partial<Entity>)
    setModalOpen(false)
    setForm({ name: '', entity_type: 'person', description: '', project_id: '', source_id: '' })
  }

  const columns = [
    { key: 'name', header: 'Name', render: (e: Entity) => <span className="text-white font-medium">{e.name}</span> },
    { key: 'entity_type', header: 'Type', render: (e: Entity) => <Badge variant="green">{e.entity_type}</Badge> },
    { key: 'description', header: 'Description', render: (e: Entity) => e.description ? <span className="text-xs text-[#8888aa] line-clamp-1">{e.description.slice(0, 80)}</span> : <span className="text-xs text-[#8888aa]">-</span> },
    { key: 'created_at', header: 'Created', render: (e: Entity) => new Date(e.created_at).toLocaleDateString() },
    { key: 'id', header: '', render: (e: Entity) => (
      <Button variant="danger" size="sm" onClick={(ev) => { ev.stopPropagation(); deleteEntity(e.id) }}>Delete</Button>
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
            className="bg-[#16213e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#e94560]"
          >
            <option value="">All projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <Button onClick={() => setModalOpen(true)}>+ New Entity</Button>
        </div>
      </div>

      <Card>
        <Table columns={columns} data={entities} keyField="id" emptyMessage="No entities yet" />
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Entity">
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-[#8888aa] mb-1">Name</label>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#e94560]"
              placeholder="Entity name"
            />
          </div>
          <div>
            <label className="block text-sm text-[#8888aa] mb-1">Type</label>
            <select
              value={form.entity_type}
              onChange={(e) => setForm({ ...form, entity_type: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#e94560]"
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
            <label className="block text-sm text-[#8888aa] mb-1">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#e94560] resize-none"
              rows={2}
              placeholder="Optional"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={!form.name.trim()}>Create</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
