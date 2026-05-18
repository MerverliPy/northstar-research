import { createBrowserRouter } from 'react-router-dom'
import App from './App'
import { ChatView } from './components/chat/ChatView'
import { DashboardView } from './components/dashboard/DashboardView'
import { ProjectsView } from './components/crud/ProjectsView'
import { SourcesView } from './components/crud/SourcesView'
import { EntitiesView } from './components/crud/EntitiesView'
import { ClaimsView } from './components/crud/ClaimsView'
import { ReportsView } from './components/crud/ReportsView'
import { GraphViewer } from './components/graph/GraphViewer'
import { CleanupView } from './components/cleanup/CleanupView'
import { ImportView } from './components/import/ImportView'
import { SettingsView } from './components/settings/SettingsView'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <ChatView /> },
      { path: 'dashboard', element: <DashboardView /> },
      { path: 'projects', element: <ProjectsView /> },
      { path: 'sources', element: <SourcesView /> },
      { path: 'entities', element: <EntitiesView /> },
      { path: 'claims', element: <ClaimsView /> },
      { path: 'reports', element: <ReportsView /> },
      { path: 'graph', element: <GraphViewer /> },
      { path: 'cleanup', element: <CleanupView /> },
      { path: 'import', element: <ImportView /> },
      { path: 'settings', element: <SettingsView /> },
    ],
  },
])
