import { useEffect, useState } from 'react'
import { useProjectStore } from '../../stores/projectStore'
import { Card } from '../shared/Card'
import { Button } from '../shared/Button'
import { Modal } from '../shared/Modal'
import { Table } from '../shared/Table'
import { Badge } from '../shared/Badge'
import type { Source } from '../../types'

export function SourcesView() {
  const { sources, projects, fetchSources, createSource, deleteSource, fetchProjects } = useProjectStore()
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState({ title: '', content: '', source_type: 'manual', project_id: '' })

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  useEffect(() => {
    if (selectedProject) {
      fetchSources(selectedProject)
    }
  }, [selectedProject, fetchSources])

  const handleSubmit = async () => {
    if (!form.title.trim() || !form.project_id) return
    setSubmitting(true)
    try {
      await createSource({
        title: form.title,
        content: form.content,
        source_type: form.source_type,
        project_id: form.project_id,
      } as Partial<Source>)
      setModalOpen(false)
      setForm({ title: '', content: '', source_type: 'manual', project_id: '' })
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
      <Button variant="danger" size="sm" onClick={(e) => { e.stopPropagation(); deleteSource(s.id) }}>Delete</Button>
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
          <Button onClick={() => { setModalOpen(true); setForm({ ...form, project_id: selectedProject }) }} disabled={!selectedProject}>
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
          <Table columns={columns} data={sources} keyField="id" emptyMessage="No sources in this project" />
        )}
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Source">
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-[#8888aa] mb-1">Title</label>
            <input
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white placeholder-[#8888aa] focus:outline-none focus:border-[#e94560] transition-colors"
              placeholder="Source title"
            />
          </div>
          <div>
            <label className="block text-sm text-[#8888aa] mb-1">Content</label>
            <textarea
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white placeholder-[#8888aa] focus:outline-none focus:border-[#e94560] transition-colors resize-none"
              rows={6}
              placeholder="Source content…"
            />
          </div>
          <div>
            <label className="block text-sm text-[#8888aa] mb-1">Type</label>
            <select
              value={form.source_type}
              onChange={(e) => setForm({ ...form, source_type: e.target.value })}
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
            <Button onClick={handleSubmit} disabled={!form.title.trim()} loading={submitting}>Create</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
