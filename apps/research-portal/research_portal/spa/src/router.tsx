import { lazy, Suspense, type ComponentType } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import App from './App'

/* eslint-disable react-refresh/only-export-components */
// Skeleton fallback for lazy-loaded views
function ViewSkeleton() {
  return (
    <div className="flex-1 flex flex-col">
      <div className="h-14 border-b flex items-center px-6" style={{ borderColor: 'var(--color-northstar-border)' }}>
        <div className="h-5 w-40 rounded animate-pulse" style={{ backgroundColor: 'var(--color-northstar-surface)' }} />
      </div>
      <div className="p-6 space-y-4">
        {[1, 2, 3].map(i => (
          <div
            key={i}
            className="h-24 rounded-lg border animate-pulse"
            style={{ backgroundColor: 'var(--color-northstar-surface)', borderColor: 'var(--color-northstar-border)' }}
          />
        ))}
      </div>
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
