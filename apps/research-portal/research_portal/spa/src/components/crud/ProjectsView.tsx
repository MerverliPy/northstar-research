import { useEffect, useState } from 'react'
import { useProjectStore } from '../../stores/projectStore'
import { useToastStore } from '../../stores/toastStore'
import { useForm, required } from '../../hooks/useForm'
import { Card } from '../shared/Card'
import { Button } from '../shared/Button'
import { Modal } from '../shared/Modal'
import { Table } from '../shared/Table'
import { Pagination } from '../shared/Pagination'
import type { Project } from '../../types'

interface ProjectForm {
  name: string
  description: string
}

export function ProjectsView() {
  const {
    projects, loading, projectsTotal, projectsPage, projectsPageSize,
    fetchProjects, createProject, updateProject, deleteProject,
  } = useProjectStore()
  const addToast = useToastStore((s) => s.addToast)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Project | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const { form, errors, setField, validateAll, resetForm } = useForm<ProjectForm>(
    { name: '', description: '' },
    { name: required('Project name is required') }
  )

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  const openCreate = () => {
    setEditing(null)
    resetForm({ name: '', description: '' })
    setModalOpen(true)
  }

  const openEdit = (project: Project) => {
    setEditing(project)
    resetForm({ name: project.name, description: project.description || '' })
    setModalOpen(true)
  }

  const handleSubmit = async () => {
    if (!validateAll()) return
    setSubmitting(true)
    try {
      if (editing) {
        await updateProject(editing.id, { name: form.name, description: form.description || null })
        addToast('Project updated', 'success')
      } else {
        await createProject({ name: form.name, description: form.description || null })
        addToast('Project created', 'success')
      }
      setModalOpen(false)
    } catch {
      addToast(editing ? 'Failed to update project' : 'Failed to create project', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const columns = [
    { key: 'name', header: 'Name', render: (p: Project) => <span className="text-white font-medium">{p.name}</span> },
    { key: 'description', header: 'Description', render: (p: Project) => p.description ? <span className="text-[#8888aa] text-xs">{p.description.slice(0, 80)}{p.description.length > 80 ? '...' : ''}</span> : <span className="text-[#8888aa] text-xs">-</span> },
    { key: 'created_at', header: 'Created', render: (p: Project) => new Date(p.created_at).toLocaleDateString() },
    { key: 'id', header: '', render: (p: Project) => (
      <div className="flex gap-2">
        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); openEdit(p) }}>Edit</Button>
        <Button variant="danger" size="sm" onClick={async (e) => { e.stopPropagation(); try { await deleteProject(p.id); addToast('Project deleted', 'success') } catch { addToast('Failed to delete project', 'error') } }}>Delete</Button>
      </div>
    )},
  ]

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-white">Projects</h1>
        <Button onClick={openCreate}>+ New Project</Button>
      </div>

      <Card variant="surface">
        <Table
          columns={columns}
          data={projects}
          keyField="id"
          loading={loading}
          emptyMessage="No projects yet"
          emptyAction={
            <Button size="sm" onClick={openCreate}>
              Create your first project
            </Button>
          }
        />
        <Pagination
          currentPage={projectsPage}
          totalPages={Math.max(1, Math.ceil(projectsTotal / projectsPageSize))}
          total={projectsTotal}
          pageSize={projectsPageSize}
          onPageChange={(p) => fetchProjects(p)}
          onPageSizeChange={(size) => fetchProjects(1, size)}
        />
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? 'Edit Project' : 'New Project'}>
        <div className="space-y-4" noValidate>
          <div>
            <label htmlFor="project-name" className="block text-sm text-[#8888aa] mb-1">Name</label>
            <input
              id="project-name"
              value={form.name}
              onChange={(e) => setField('name', e.target.value)}
              className={`w-full bg-[#1a1a2e] border rounded-md px-3 py-2 text-sm text-white placeholder-[#8888aa] focus:outline-none focus:border-[#e94560] transition-colors ${errors.name ? 'border-red-500' : 'border-[#2a2a4a]'}`}
              placeholder="Project name"
              aria-invalid={!!errors.name}
              aria-describedby={errors.name ? 'project-name-error' : undefined}
            />
            {errors.name && (
              <span id="project-name-error" className="block text-xs text-red-400 mt-1">{errors.name}</span>
            )}
          </div>
          <div>
            <label htmlFor="project-desc" className="block text-sm text-[#8888aa] mb-1">Description</label>
            <textarea
              id="project-desc"
              value={form.description}
              onChange={(e) => setField('description', e.target.value)}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white placeholder-[#8888aa] focus:outline-none focus:border-[#e94560] transition-colors resize-none"
              rows={3}
              placeholder="Optional description"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button onClick={handleSubmit} loading={submitting}>
              {editing ? 'Update' : 'Create'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
