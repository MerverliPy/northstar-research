import { useEffect, useState } from 'react'
import { useProjectStore } from '../../stores/projectStore'
import { Card } from '../shared/Card'
import { Button } from '../shared/Button'
import { Modal } from '../shared/Modal'
import { Table } from '../shared/Table'
import type { Report } from '../../types'

export function ReportsView() {
  const { reports, projects, fetchReports, createReport, deleteReport, fetchProjects } = useProjectStore()
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedProject, setSelectedProject] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState({ title: '', content: '', report_type: 'summary', project_id: '' })

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  useEffect(() => {
    if (selectedProject) fetchReports(selectedProject)
  }, [selectedProject, fetchReports])

  const handleSubmit = async () => {
    if (!form.title.trim() || !form.project_id) return
    setSubmitting(true)
    try {
      await createReport({
        title: form.title,
        content: form.content,
        report_type: form.report_type,
        project_id: form.project_id,
      } as Partial<Report>)
      setModalOpen(false)
      setForm({ title: '', content: '', report_type: 'summary', project_id: '' })
    } finally {
      setSubmitting(false)
    }
  }

  const columns = [
    { key: 'title', header: 'Title', render: (r: Report) => <span className="text-white font-medium">{r.title}</span> },
    { key: 'report_type', header: 'Type', render: (r: Report) => <span className="text-xs text-[#8888aa]">{r.report_type}</span> },
    { key: 'created_at', header: 'Created', render: (r: Report) => new Date(r.created_at).toLocaleDateString() },
    { key: 'id', header: '', render: (r: Report) => (
      <Button variant="danger" size="sm" onClick={(e) => { e.stopPropagation(); deleteReport(r.id) }}>Delete</Button>
    )},
  ]

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-white">Reports</h1>
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
            + New Report
          </Button>
        </div>
      </div>

      <Card variant="surface">
        {!selectedProject ? (
          <div className="flex flex-col items-center gap-3 py-8">
            <svg className="w-10 h-10 text-[#2a2a4a]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            <p className="text-sm text-[#8888aa]">Select a project to view its reports</p>
          </div>
        ) : (
          <Table columns={columns} data={reports} keyField="id" emptyMessage="No reports yet" />
        )}
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Report">
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-[#8888aa] mb-1">Title</label>
            <input
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white placeholder-[#8888aa] focus:outline-none focus:border-[#e94560] transition-colors"
              placeholder="Report title"
            />
          </div>
          <div>
            <label className="block text-sm text-[#8888aa] mb-1">Type</label>
            <select
              value={form.report_type}
              onChange={(e) => setForm({ ...form, report_type: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#e94560] transition-colors"
            >
              <option value="summary">Summary</option>
              <option value="analysis">Analysis</option>
              <option value="quality">Quality</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-[#8888aa] mb-1">Content</label>
            <textarea
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white placeholder-[#8888aa] focus:outline-none focus:border-[#e94560] transition-colors resize-none"
              rows={6}
              placeholder="Report content…"
            />
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
