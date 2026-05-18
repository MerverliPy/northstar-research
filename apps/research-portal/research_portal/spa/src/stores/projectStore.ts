import { create } from 'zustand'
import type {
  Project, Source, Entity, Claim, Report,
  DashboardStats, PaginatedResponse,
} from '../types'

const API_BASE = '/api/v1'

async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `HTTP ${res.status}`)
  }
  return res.json()
}

interface ProjectState {
  projects: Project[]
  sources: Source[]
  entities: Entity[]
  claims: Claim[]
  reports: Report[]
  stats: DashboardStats | null
  loading: boolean

  fetchStats: () => Promise<void>

  fetchProjects: () => Promise<void>
  createProject: (data: Partial<Project>) => Promise<Project>
  updateProject: (id: string, data: Partial<Project>) => Promise<Project>
  deleteProject: (id: string) => Promise<void>

  fetchSources: (projectId: string) => Promise<void>
  createSource: (data: Partial<Source>) => Promise<Source>
  deleteSource: (id: string) => Promise<void>

  fetchEntities: (filters?: { source_id?: string; project_id?: string }) => Promise<void>
  createEntity: (data: Partial<Entity>) => Promise<Entity>
  deleteEntity: (id: string) => Promise<void>

  fetchClaims: (filters?: { source_id?: string; entity_id?: string }) => Promise<void>
  createClaim: (data: Partial<Claim>) => Promise<Claim>
  deleteClaim: (id: string) => Promise<void>

  fetchReports: (projectId: string) => Promise<void>
  createReport: (data: Partial<Report>) => Promise<Report>
  deleteReport: (id: string) => Promise<void>
}

export const useProjectStore = create<ProjectState>((set) => ({
  projects: [],
  sources: [],
  entities: [],
  claims: [],
  reports: [],
  stats: null,
  loading: false,

  fetchStats: async () => {
    const [projects, sources, entities, claims] = await Promise.all([
      apiFetch<PaginatedResponse<Project>>('/projects/?limit=1'),
      apiFetch<PaginatedResponse<Source>>('/sources/?project_id=all&limit=1'),
      apiFetch<PaginatedResponse<Entity>>('/entities/?limit=1'),
      apiFetch<PaginatedResponse<Claim>>('/claims/?limit=1'),
    ])
    set({
      stats: {
        projects: projects.total,
        sources: sources.total,
        entities: entities.total,
        claims: claims.total,
        reports: 0,
      },
    })
  },

  fetchProjects: async () => {
    const data = await apiFetch<PaginatedResponse<Project>>('/projects/?limit=100')
    set({ projects: data.items })
  },

  createProject: async (data) => {
    const project = await apiFetch<Project>('/projects/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
    set((state) => ({ projects: [project, ...state.projects] }))
    return project
  },

  updateProject: async (id, data) => {
    const project = await apiFetch<Project>(`/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
    set((state) => ({
      projects: state.projects.map((p) => (p.id === id ? project : p)),
    }))
    return project
  },

  deleteProject: async (id) => {
    await apiFetch(`/projects/${id}`, { method: 'DELETE' })
    set((state) => ({
      projects: state.projects.filter((p) => p.id !== id),
    }))
  },

  fetchSources: async (projectId) => {
    const data = await apiFetch<PaginatedResponse<Source>>(
      `/sources/?project_id=${projectId}&limit=100`
    )
    set({ sources: data.items })
  },

  createSource: async (data) => {
    const source = await apiFetch<Source>('/sources/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
    set((state) => ({ sources: [source, ...state.sources] }))
    return source
  },

  deleteSource: async (id) => {
    await apiFetch(`/sources/${id}`, { method: 'DELETE' })
    set((state) => ({
      sources: state.sources.filter((s) => s.id !== id),
    }))
  },

  fetchEntities: async (filters) => {
    const params = new URLSearchParams()
    if (filters?.source_id) params.set('source_id', filters.source_id)
    if (filters?.project_id) params.set('project_id', filters.project_id)
    params.set('limit', '100')
    const data = await apiFetch<PaginatedResponse<Entity>>(`/entities/?${params}`)
    set({ entities: data.items })
  },

  createEntity: async (data) => {
    const entity = await apiFetch<Entity>('/entities/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
    set((state) => ({ entities: [entity, ...state.entities] }))
    return entity
  },

  deleteEntity: async (id) => {
    await apiFetch(`/entities/${id}`, { method: 'DELETE' })
    set((state) => ({
      entities: state.entities.filter((e) => e.id !== id),
    }))
  },

  fetchClaims: async (filters) => {
    const params = new URLSearchParams()
    if (filters?.source_id) params.set('source_id', filters.source_id)
    if (filters?.entity_id) params.set('entity_id', filters.entity_id)
    params.set('limit', '100')
    const data = await apiFetch<PaginatedResponse<Claim>>(`/claims/?${params}`)
    set({ claims: data.items })
  },

  createClaim: async (data) => {
    const claim = await apiFetch<Claim>('/claims/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
    set((state) => ({ claims: [claim, ...state.claims] }))
    return claim
  },

  deleteClaim: async (id) => {
    await apiFetch(`/claims/${id}`, { method: 'DELETE' })
    set((state) => ({
      claims: state.claims.filter((c) => c.id !== id),
    }))
  },

  fetchReports: async (projectId) => {
    const data = await apiFetch<PaginatedResponse<Report>>(
      `/reports/?project_id=${projectId}&limit=100`
    )
    set({ reports: data.items })
  },

  createReport: async (data) => {
    const report = await apiFetch<Report>('/reports/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
    set((state) => ({ reports: [report, ...state.reports] }))
    return report
  },

  deleteReport: async (id) => {
    await apiFetch(`/reports/${id}`, { method: 'DELETE' })
    set((state) => ({
      reports: state.reports.filter((r) => r.id !== id),
    }))
  },
}))
