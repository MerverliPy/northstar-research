import { Outlet } from 'react-router-dom'

export function MainPanel() {
  return (
    <main className="flex-1 overflow-hidden flex flex-col">
      <Outlet />
    </main>
  )
}
