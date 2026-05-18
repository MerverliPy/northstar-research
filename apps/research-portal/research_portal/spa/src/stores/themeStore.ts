import { create } from 'zustand'

export type Theme = 'light' | 'dark' | 'system'
type ResolvedTheme = 'light' | 'dark'

function getSystemTheme(): ResolvedTheme {
  if (typeof window === 'undefined') return 'dark'
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
}

function applyTheme(resolved: ResolvedTheme) {
  const root = document.documentElement
  if (resolved === 'dark') {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
}

function resolveTheme(theme: Theme): ResolvedTheme {
  if (theme === 'system') return getSystemTheme()
  return theme
}

interface ThemeState {
  theme: Theme
  resolved: ResolvedTheme
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}

const stored = (typeof window !== 'undefined' ? localStorage.getItem('northstar-theme') : null) as Theme | null
const initial: Theme = stored || 'system'
const resolved = resolveTheme(initial)

// Apply immediately to avoid flash
if (typeof window !== 'undefined') {
  applyTheme(resolved)
}

export const useThemeStore = create<ThemeState>((set) => ({
  theme: initial,
  resolved,
  setTheme: (theme) => {
    const newResolved = resolveTheme(theme)
    applyTheme(newResolved)
    localStorage.setItem('northstar-theme', theme)
    set({ theme, resolved: newResolved })
  },
  toggleTheme: () => {
    set((state) => {
      const nextResolved: ResolvedTheme = state.resolved === 'dark' ? 'light' : 'dark'
      const nextTheme: Theme = nextResolved
      applyTheme(nextResolved)
      localStorage.setItem('northstar-theme', nextTheme)
      return { theme: nextTheme, resolved: nextResolved }
    })
  },
}))

// Listen for system theme changes when in 'system' mode
if (typeof window !== 'undefined') {
  window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => {
    const state = useThemeStore.getState()
    if (state.theme === 'system') {
      const newResolved = getSystemTheme()
      applyTheme(newResolved)
      useThemeStore.setState({ resolved: newResolved })
    }
  })
}
