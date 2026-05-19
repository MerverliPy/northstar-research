import { NavLink } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useThemeStore } from '../stores/themeStore'
import { useInstallPrompt } from '../hooks/useInstallPrompt'

interface NavLinkDef {
  to: string
  label: string
  icon: React.ReactNode
}

const iconClass = "w-[18px] h-[18px] flex-shrink-0"

const links: NavLinkDef[] = [
  {
    to: '/', label: 'Chat',
    icon: <svg className={iconClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>,
  },
  {
    to: '/dashboard', label: 'Dashboard',
    icon: <svg className={iconClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>,
  },
  {
    to: '/projects', label: 'Projects',
    icon: <svg className={iconClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>,
  },
  {
    to: '/sources', label: 'Sources',
    icon: <svg className={iconClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>,
  },
  {
    to: '/entities', label: 'Entities',
    icon: <svg className={iconClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 7h-4.5L15 4h-6l-.5 3H4v3h5.5l.5-3h4l.5 3H20V7z"/><circle cx="9" cy="16" r="2"/><circle cx="15" cy="16" r="2"/><path d="M9 16h6"/></svg>,
  },
  {
    to: '/claims', label: 'Claims',
    icon: <svg className={iconClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>,
  },
  {
    to: '/reports', label: 'Reports',
    icon: <svg className={iconClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>,
  },
  {
    to: '/graph', label: 'Graph',
    icon: <svg className={iconClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>,
  },
  {
    to: '/cleanup', label: 'Cleanup',
    icon: <svg className={iconClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/><path d="M13 13l6 6"/></svg>,
  },
  {
    to: '/import', label: 'Import',
    icon: <svg className={iconClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>,
  },
  {
    to: '/settings', label: 'Settings',
    icon: <svg className={iconClass} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>,
  },
]

function InstallButton({ collapsed }: { collapsed: boolean }) {
  const { isInstallable, promptInstall } = useInstallPrompt()

  if (!isInstallable) return null

  return (
    <div className="border-t p-2" style={{ borderColor: 'var(--color-sidebar-border)' }}>
      <button
        onClick={promptInstall}
        className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm rounded-md transition-colors ${
          collapsed ? 'justify-center px-0' : ''
        }`}
        style={{ color: 'var(--color-sidebar-text)' }}
        onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--color-sidebar-hover)' }}
        onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '' }}
        aria-label="Install app"
        title="Install Northstar as an app"
      >
        <svg className="w-[18px] h-[18px] flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="7 10 12 15 17 10" />
          <line x1="12" y1="15" x2="12" y2="3" />
        </svg>
        {!collapsed && <span>Install App</span>}
      </button>
    </div>
  )
}

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const { resolved: theme, toggleTheme } = useThemeStore()

  // Auto-collapse sidebar on narrow viewports (<=768px), auto-expand on wider
  useEffect(() => {
    const mq = window.matchMedia('(max-width: 768px)')

    const handleChange = (e: MediaQueryListEvent | { matches: boolean }) => {
      if (e.matches) {
        setCollapsed(true)
      } else {
        setCollapsed(false)
      }
    }

    handleChange(mq)
    mq.addEventListener('change', handleChange)
    return () => mq.removeEventListener('change', handleChange)
  }, [])

  return (
    <aside
      className={`flex flex-col border-r transition-all duration-200 flex-shrink-0 ${
        collapsed ? 'w-14' : 'w-56'
      }`}
      style={{
        backgroundColor: 'var(--color-sidebar-bg)',
        borderColor: 'var(--color-sidebar-border)',
      }}
    >
      <div
        className="flex items-center justify-between h-14 px-4 border-b"
        style={{ borderColor: 'var(--color-sidebar-border)' }}
      >
        {!collapsed && (
          <span className="font-bold text-[#e94560] text-sm tracking-wider">NORTHSTAR</span>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-[#8888aa] hover:text-white text-sm w-7 h-7 flex items-center justify-center rounded-md transition-colors"
          style={{ backgroundColor: collapsed ? undefined : undefined }}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
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
              `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors group relative ${
                isActive
                  ? 'bg-[#e94560]/10 text-[#e94560] border-r-2 border-[#e94560]'
                  : ''
              } ${collapsed ? 'justify-center px-0' : ''}`
            }
            style={({ isActive }) => ({
              color: isActive ? 'var(--color-sidebar-active-text)' : 'var(--color-sidebar-text)',
              backgroundColor: isActive ? 'var(--color-sidebar-active-bg)' : undefined,
            })}
            aria-label={collapsed ? link.label : undefined}
            title={collapsed ? link.label : undefined}
            onMouseEnter={(e) => {
              if (!e.currentTarget.classList.contains('bg-\\[\\#e94560\\]\\/10')) {
                e.currentTarget.style.backgroundColor = 'var(--color-sidebar-hover)'
              }
            }}
            onMouseLeave={(e) => {
              if (!e.currentTarget.classList.contains('bg-\\[\\#e94560\\]\\/10')) {
                e.currentTarget.style.backgroundColor = ''
              }
            }}
          >
            {link.icon}
            {!collapsed && <span>{link.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Install button */}
      <InstallButton collapsed={collapsed} />

      {/* Theme toggle */}
      <div className="border-t p-2 pb-[calc(0.5rem+env(safe-area-inset-bottom,0px))]" style={{ borderColor: 'var(--color-sidebar-border)' }}>
        <button
          onClick={toggleTheme}
          className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm rounded-md transition-colors ${
            collapsed ? 'justify-center px-0' : ''
          }`}
          style={{ color: 'var(--color-sidebar-text)' }}
          onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--color-sidebar-hover)' }}
          onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '' }}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? (
            <svg className="w-[18px] h-[18px] flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
            </svg>
          ) : (
            <svg className="w-[18px] h-[18px] flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          )}
          {!collapsed && <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>}
        </button>
      </div>
    </aside>
  )
}
