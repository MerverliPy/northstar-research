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
import type { Source } from '../../types'

interface SourceForm {
  title: string
  content: string
  source_type: string
  project_id: string
}

export function SourcesView() {
  const {
    sources, projects, sourcesTotal, sourcesPage, sourcesPageSize,
    fetchSources, createSource, deleteSource, fetchProjects,
  } = useProjectStore()
  const addToast = useToastStore((s) => s.addToast)
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [submitting, setSubmitting] = useState(false)
  const { form, errors, setField, validateAll, resetForm } = useForm<SourceForm>(
    { title: '', content: '', source_type: 'manual', project_id: '' },
    { title: required('Title is required') }
  )

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  useEffect(() => {
    if (selectedProject) {
      fetchSources(selectedProject)
    }
  }, [selectedProject, fetchSources])

  const handleSubmit = async () => {
    if (!validateAll() || !form.project_id) return
    setSubmitting(true)
    try {
      await createSource({
        title: form.title,
        content: form.content,
        source_type: form.source_type,
        project_id: form.project_id,
      } as Partial<Source>)
      addToast('Source created', 'success')
      setModalOpen(false)
      resetForm({ title: '', content: '', source_type: 'manual', project_id: '' })
    } catch {
      addToast('Failed to create source', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const columns = [
    { key: 'title', header: 'Title', render: (s: Source) => <span className="text-white font-medium">{s.title}</span> },
    { key: 'source_type', header: 'Type', render: (s: Source) => <Badge variant="blue">{s.source_type}</Badge> },
    { key: 'content', header: 'Content', render: (s: Source) => <span className="text-xs text-[#8888aa] line-clamp-1">{s.content.slice(0, 100)}</span> },
    { key: 'created_at', header: 'Created', render: (s: Source) => new Date(s.created_at).toLocaleDateString() },
    { key: 'id', header: '', render: (s: Source) => (
      <Button variant="danger" size="sm" onClick={async (e) => { e.stopPropagation(); try { await deleteSource(s.id); addToast('Source deleted', 'success') } catch { addToast('Failed to delete source', 'error') } }}>Delete</Button>
    )},
  ]

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-white">Sources</h1>
        <div className="flex gap-3">
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="bg-[#16213e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#e94560] transition-colors"
          >
            <option value="">Select project…</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <Button onClick={() => { setModalOpen(true); setField('project_id', selectedProject) }} disabled={!selectedProject}>
            + New Source
          </Button>
        </div>
      </div>

      <Card variant="surface">
        {!selectedProject ? (
          <div className="flex flex-col items-center gap-3 py-8">
            <svg className="w-10 h-10 text-[#2a2a4a]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            <p className="text-sm text-[#8888aa]">Select a project to view its sources</p>
          </div>
        ) : (
          <>
            <Table columns={columns} data={sources} keyField="id" emptyMessage="No sources in this project" />
            <Pagination
              currentPage={sourcesPage}
              totalPages={Math.max(1, Math.ceil(sourcesTotal / sourcesPageSize))}
              total={sourcesTotal}
              pageSize={sourcesPageSize}
              onPageChange={(p) => { if (selectedProject) fetchSources(selectedProject, p) }}
              onPageSizeChange={(size) => { if (selectedProject) fetchSources(selectedProject, 1, size) }}
            />
          </>
        )}
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Source">
        <form className="space-y-4" noValidate onSubmit={(e) => { e.preventDefault(); handleSubmit() }}>
          <div>
            <label htmlFor="source-title" className="block text-sm text-[#8888aa] mb-1">Title</label>
            <input
              id="source-title"
              value={form.title}
              onChange={(e) => setField('title', e.target.value)}
              className={`w-full bg-[#1a1a2e] border rounded-md px-3 py-2 text-sm text-white placeholder-[#8888aa] focus:outline-none focus:border-[#e94560] transition-colors ${errors.title ? 'border-red-500' : 'border-[#2a2a4a]'}`}
              placeholder="Source title"
              aria-invalid={!!errors.title}
              aria-describedby={errors.title ? 'source-title-error' : undefined}
            />
            {errors.title && (
              <span id="source-title-error" className="block text-xs text-red-400 mt-1">{errors.title}</span>
            )}
          </div>
          <div>
            <label htmlFor="source-content" className="block text-sm text-[#8888aa] mb-1">Content</label>
            <textarea
              id="source-content"
              value={form.content}
              onChange={(e) => setField('content', e.target.value)}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white placeholder-[#8888aa] focus:outline-none focus:border-[#e94560] transition-colors resize-none"
              rows={6}
              placeholder="Source content…"
            />
          </div>
          <div>
            <label htmlFor="source-type" className="block text-sm text-[#8888aa] mb-1">Type</label>
            <select
              id="source-type"
              value={form.source_type}
              onChange={(e) => setField('source_type', e.target.value)}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#e94560] transition-colors"
            >
              <option value="manual">Manual</option>
              <option value="paste">Paste</option>
              <option value="url">URL</option>
              <option value="file">File</option>
            </select>
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
