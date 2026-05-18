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

  // Pagination state
  projectsTotal: number
  projectsPage: number
  projectsPageSize: number

  sourcesTotal: number
  sourcesPage: number
  sourcesPageSize: number

  entitiesTotal: number
  entitiesPage: number
  entitiesPageSize: number

  claimsTotal: number
  claimsPage: number
  claimsPageSize: number

  reportsTotal: number
  reportsPage: number
  reportsPageSize: number

  fetchStats: () => Promise<void>

  fetchProjects: (page?: number, pageSize?: number) => Promise<void>
  createProject: (data: Partial<Project>) => Promise<Project>
  updateProject: (id: string, data: Partial<Project>) => Promise<Project>
  deleteProject: (id: string) => Promise<void>

  fetchSources: (projectId: string, page?: number, pageSize?: number) => Promise<void>
  createSource: (data: Partial<Source>) => Promise<Source>
  deleteSource: (id: string) => Promise<void>

  fetchEntities: (filters?: { source_id?: string; project_id?: string }, page?: number, pageSize?: number) => Promise<void>
  createEntity: (data: Partial<Entity>) => Promise<Entity>
  deleteEntity: (id: string) => Promise<void>

  fetchClaims: (filters?: { source_id?: string; entity_id?: string }, page?: number, pageSize?: number) => Promise<void>
  createClaim: (data: Partial<Claim>) => Promise<Claim>
  deleteClaim: (id: string) => Promise<void>

  fetchReports: (projectId: string, page?: number, pageSize?: number) => Promise<void>
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

  projectsTotal: 0,
  projectsPage: 1,
  projectsPageSize: 25,

  sourcesTotal: 0,
  sourcesPage: 1,
  sourcesPageSize: 25,

  entitiesTotal: 0,
  entitiesPage: 1,
  entitiesPageSize: 25,

  claimsTotal: 0,
  claimsPage: 1,
  claimsPageSize: 25,

  reportsTotal: 0,
  reportsPage: 1,
  reportsPageSize: 25,

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

  fetchProjects: async (page, pageSize) => {
    set({ loading: true })
    try {
      const pg = page ?? useProjectStore.getState().projectsPage
      const ps = pageSize ?? useProjectStore.getState().projectsPageSize
      const offset = (pg - 1) * ps
      const data = await apiFetch<PaginatedResponse<Project>>(`/projects/?limit=${ps}&offset=${offset}`)
      set({
        projects: data.items,
        projectsTotal: data.total,
        projectsPage: pg,
        projectsPageSize: ps,
      })
    } finally {
      set({ loading: false })
    }
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

  fetchSources: async (projectId, page, pageSize) => {
    const pg = page ?? useProjectStore.getState().sourcesPage
    const ps = pageSize ?? useProjectStore.getState().sourcesPageSize
    const offset = (pg - 1) * ps
    const data = await apiFetch<PaginatedResponse<Source>>(
      `/sources/?project_id=${projectId}&limit=${ps}&offset=${offset}`
    )
    set({
      sources: data.items,
      sourcesTotal: data.total,
      sourcesPage: pg,
      sourcesPageSize: ps,
    })
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

  fetchEntities: async (filters, page, pageSize) => {
    const pg = page ?? useProjectStore.getState().entitiesPage
    const ps = pageSize ?? useProjectStore.getState().entitiesPageSize
    const offset = (pg - 1) * ps
    const params = new URLSearchParams()
    if (filters?.source_id) params.set('source_id', filters.source_id)
    if (filters?.project_id) params.set('project_id', filters.project_id)
    params.set('limit', String(ps))
    params.set('offset', String(offset))
    const data = await apiFetch<PaginatedResponse<Entity>>(`/entities/?${params}`)
    set({
      entities: data.items,
      entitiesTotal: data.total,
      entitiesPage: pg,
      entitiesPageSize: ps,
    })
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

  fetchClaims: async (filters, page, pageSize) => {
    const pg = page ?? useProjectStore.getState().claimsPage
    const ps = pageSize ?? useProjectStore.getState().claimsPageSize
    const offset = (pg - 1) * ps
    const params = new URLSearchParams()
    if (filters?.source_id) params.set('source_id', filters.source_id)
    if (filters?.entity_id) params.set('entity_id', filters.entity_id)
    params.set('limit', String(ps))
    params.set('offset', String(offset))
    const data = await apiFetch<PaginatedResponse<Claim>>(`/claims/?${params}`)
    set({
      claims: data.items,
      claimsTotal: data.total,
      claimsPage: pg,
      claimsPageSize: ps,
    })
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

  fetchReports: async (projectId, page, pageSize) => {
    const pg = page ?? useProjectStore.getState().reportsPage
    const ps = pageSize ?? useProjectStore.getState().reportsPageSize
    const offset = (pg - 1) * ps
    const data = await apiFetch<PaginatedResponse<Report>>(
      `/reports/?project_id=${projectId}&limit=${ps}&offset=${offset}`
    )
    set({
      reports: data.items,
      reportsTotal: data.total,
      reportsPage: pg,
      reportsPageSize: ps,
    })
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
