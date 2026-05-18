import { NavLink } from 'react-router-dom'
import { useState } from 'react'

const links = [
  { to: '/', label: 'Chat', icon: '💬' },
  { to: '/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/projects', label: 'Projects', icon: '📁' },
  { to: '/sources', label: 'Sources', icon: '📄' },
  { to: '/entities', label: 'Entities', icon: '🏷️' },
  { to: '/claims', label: 'Claims', icon: '📝' },
  { to: '/reports', label: 'Reports', icon: '📋' },
  { to: '/graph', label: 'Graph', icon: '🔗' },
  { to: '/cleanup', label: 'Cleanup', icon: '🧹' },
  { to: '/import', label: 'Import', icon: '📥' },
  { to: '/settings', label: 'Settings', icon: '⚙️' },
]

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={`flex flex-col bg-[#0f0f23] border-r border-[#2a2a4a] transition-all duration-200 ${collapsed ? 'w-14' : 'w-56'}`}
    >
      <div className="flex items-center justify-between h-14 px-4 border-b border-[#2a2a4a]">
        {!collapsed && (
          <span className="font-bold text-[#e94560] text-sm">NORTHSTAR</span>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-[#8888aa] hover:text-white text-sm"
        >
          {collapsed ? '▶' : '◀'}
        </button>
      </div>
      <nav className="flex-1 overflow-y-auto py-2">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                isActive
                  ? 'bg-[#e94560]/10 text-[#e94560] border-r-2 border-[#e94560]'
                  : 'text-[#8888aa] hover:text-white hover:bg-[#2a2a4a]/30'
              } ${collapsed ? 'justify-center px-0' : ''}`
            }
          >
            <span className="text-base">{link.icon}</span>
            {!collapsed && <span>{link.label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
