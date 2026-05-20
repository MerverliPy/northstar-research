import { Sidebar } from './components/Sidebar'
import { MainPanel } from './components/layout/MainPanel'
import { ToastContainer } from './components/shared/Toast'
import { OfflineBanner } from './components/shared/OfflineBanner'
import { usePWA } from './hooks/usePWA'

export default function App() {
  usePWA()

  return (
    <div className="flex h-full">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:top-0 focus:left-0 focus:z-50 focus:px-4 focus:py-2 focus:bg-[--color-northstar-accent] focus:text-white focus:no-underline">Skip to main content</a>
      <OfflineBanner />
      <Sidebar />
      <main id="main-content" className="flex-1 overflow-auto">
        <MainPanel />
      </main>
      <ToastContainer />
    </div>
  )
}
