import { Sidebar } from './components/Sidebar'
import { MainPanel } from './components/layout/MainPanel'
import { ToastContainer } from './components/shared/Toast'
import { OfflineBanner } from './components/shared/OfflineBanner'
import { usePWA } from './hooks/usePWA'

export default function App() {
  usePWA()

  return (
    <div className="flex h-full">
      <OfflineBanner />
      <Sidebar />
      <MainPanel />
      <ToastContainer />
    </div>
  )
}
