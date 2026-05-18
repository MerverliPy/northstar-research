import { Outlet } from 'react-router-dom'

export function MainPanel() {
  return (
    <main className="flex-1 overflow-hidden flex flex-col bg-[#1a1a2e]">
      {/* Subtle top accent line */}
      <div className="h-0.5 bg-gradient-to-r from-[#e94560]/0 via-[#e94560]/50 to-[#e94560]/0 flex-shrink-0" />
      <div className="flex-1 overflow-hidden">
        <Outlet />
      </div>
    </main>
  )
}
