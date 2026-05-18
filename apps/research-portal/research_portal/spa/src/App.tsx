import { Sidebar } from './components/Sidebar'
import { MainPanel } from './components/layout/MainPanel'

export default function App() {
  return (
    <div className="flex h-full">
      <Sidebar />
      <MainPanel />
    </div>
  )
}
