import { useEffect, useState } from 'react'
import { useProjectStore } from '../../stores/projectStore'
import { useToastStore } from '../../stores/toastStore'
import { useForm, required } from '../../hooks/useForm'
import { Card } from '../shared/Card'
import { Button } from '../shared/Button'
import { Modal } from '../shared/Modal'
import { Table } from '../shared/Table'
import { Pagination } from '../shared/Pagination'
import type { Report } from '../../types'

interface ReportForm {
  title: string
  content: string
  report_type: string
  project_id: string
}

export function ReportsView() {
  const {
    reports, projects, reportsTotal, reportsPage, reportsPageSize,
    fetchReports, createReport, deleteReport, fetchProjects,
  } = useProjectStore()
  const addToast = useToastStore((s) => s.addToast)
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedProject, setSelectedProject] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { form, errors, setField, validateAll, resetForm } = useForm<ReportForm>(
    { title: '', content: '', report_type: 'summary', project_id: '' },
    { title: required('Report title is required') }
  )

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  useEffect(() => {
    if (selectedProject) fetchReports(selectedProject)
  }, [selectedProject, fetchReports])

  const handleSubmit = async () => {
    if (!validateAll() || !form.project_id) return
    setSubmitting(true)
    try {
      await createReport({
        title: form.title,
        content: form.content,
        report_type: form.report_type,
        project_id: form.project_id,
      } as Partial<Report>)
      addToast('Report created', 'success')
      setModalOpen(false)
      resetForm({ title: '', content: '', report_type: 'summary', project_id: '' })
    } catch {
      addToast('Failed to create report', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const columns = [
    { key: 'title', header: 'Title', render: (r: Report) => <span className="text-white font-medium">{r.title}</span> },
    { key: 'report_type', header: 'Type', render: (r: Report) => <span className="text-xs text-[#8888aa]">{r.report_type}</span> },
    { key: 'created_at', header: 'Created', render: (r: Report) => new Date(r.created_at).toLocaleDateString() },
    { key: 'id', header: '', render: (r: Report) => (
      <Button variant="danger" size="sm" onClick={async (e) => { e.stopPropagation(); try { await deleteReport(r.id); addToast('Report deleted', 'success') } catch { addToast('Failed to delete report', 'error') } }}>Delete</Button>
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
          <Button onClick={() => { setModalOpen(true); setField('project_id', selectedProject) }} disabled={!selectedProject}>
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
          <>
            <Table columns={columns} data={reports} keyField="id" emptyMessage="No reports yet" />
            <Pagination
              currentPage={reportsPage}
              totalPages={Math.max(1, Math.ceil(reportsTotal / reportsPageSize))}
              total={reportsTotal}
              pageSize={reportsPageSize}
              onPageChange={(p) => { if (selectedProject) fetchReports(selectedProject, p) }}
              onPageSizeChange={(size) => { if (selectedProject) fetchReports(selectedProject, 1, size) }}
            />
          </>
        )}
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Report">
        <form className="space-y-4" noValidate onSubmit={(e) => { e.preventDefault(); handleSubmit() }}>
          <div>
            <label htmlFor="report-title" className="block text-sm text-[#8888aa] mb-1">Title</label>
            <input
              id="report-title"
              value={form.title}
              onChange={(e) => setField('title', e.target.value)}
              className={`w-full bg-[#1a1a2e] border rounded-md px-3 py-2 text-sm text-white placeholder-[#8888aa] focus:outline-none focus:border-[#e94560] transition-colors ${errors.title ? 'border-red-500' : 'border-[#2a2a4a]'}`}
              placeholder="Report title"
              aria-invalid={!!errors.title}
              aria-describedby={errors.title ? 'report-title-error' : undefined}
            />
            {errors.title && (
              <span id="report-title-error" className="block text-xs text-red-400 mt-1">{errors.title}</span>
            )}
          </div>
          <div>
            <label htmlFor="report-type" className="block text-sm text-[#8888aa] mb-1">Type</label>
            <select
              id="report-type"
              value={form.report_type}
              onChange={(e) => setField('report_type', e.target.value)}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#e94560] transition-colors"
            >
              <option value="summary">Summary</option>
              <option value="analysis">Analysis</option>
              <option value="quality">Quality</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          <div>
            <label htmlFor="report-content" className="block text-sm text-[#8888aa] mb-1">Content</label>
            <textarea
              id="report-content"
              value={form.content}
              onChange={(e) => setField('content', e.target.value)}
              className="w-full bg-[#1a1a2e] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-white placeholder-[#8888aa] focus:outline-none focus:border-[#e94560] transition-colors resize-none"
              rows={6}
              placeholder="Report content…"
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
