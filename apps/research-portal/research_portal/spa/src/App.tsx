import { Sidebar } from './components/Sidebar'
import { MainPanel } from './components/layout/MainPanel'
import { ToastContainer } from './components/shared/Toast'

export default function App() {
  return (
    <div className="flex h-full">
      <Sidebar />
      <MainPanel />
      <ToastContainer />
    </div>
  )
}
