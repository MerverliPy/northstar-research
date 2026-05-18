import { lazy, Suspense, type ComponentType } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import App from './App'

/* eslint-disable react-refresh/only-export-components */
// Skeleton fallback for lazy-loaded views
function ViewSkeleton() {
  return (
    <div className="flex flex-col h-full overflow-y-auto p-6 animate-pulse">
      <div className="h-8 w-48 skeleton rounded mb-6" />
      <div className="h-64 skeleton rounded-lg" />
    </div>
  )
}

function lazyView(importFn: () => Promise<{ [key: string]: ComponentType<unknown> }>, exportName: string) {
  const LazyComp = lazy(() =>
    importFn().then((mod) => ({ default: mod[exportName] as ComponentType<unknown> }))
  )
  return (
    <Suspense fallback={<ViewSkeleton />}>
      <LazyComp />
    </Suspense>
  )
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: lazyView(() => import('./components/chat/ChatView'), 'ChatView') },
      { path: 'dashboard', element: lazyView(() => import('./components/dashboard/DashboardView'), 'DashboardView') },
      { path: 'projects', element: lazyView(() => import('./components/crud/ProjectsView'), 'ProjectsView') },
      { path: 'sources', element: lazyView(() => import('./components/crud/SourcesView'), 'SourcesView') },
      { path: 'entities', element: lazyView(() => import('./components/crud/EntitiesView'), 'EntitiesView') },
      { path: 'claims', element: lazyView(() => import('./components/crud/ClaimsView'), 'ClaimsView') },
      { path: 'reports', element: lazyView(() => import('./components/crud/ReportsView'), 'ReportsView') },
      { path: 'graph', element: lazyView(() => import('./components/graph/GraphViewer'), 'GraphViewer') },
      { path: 'cleanup', element: lazyView(() => import('./components/cleanup/CleanupView'), 'CleanupView') },
      { path: 'import', element: lazyView(() => import('./components/import/ImportView'), 'ImportView') },
      { path: 'settings', element: lazyView(() => import('./components/settings/SettingsView'), 'SettingsView') },
    ],
  },
])
