import { create } from 'zustand'
import type { Settings } from '../types'

interface SettingsState {
  settings: Settings
  loading: boolean
  fetchSettings: () => Promise<void>
  toggleGate: (gate: 'force_graph_extraction' | 'enable_destructive_cleanup') => Promise<void>
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  settings: {
    force_graph_extraction: false,
    enable_destructive_cleanup: false,
    research_agent_url: 'http://127.0.0.1:8099',
    chat_import_bridge_url: 'http://127.0.0.1:3022',
    log_level: 'INFO',
  },
  loading: false,

  fetchSettings: async () => {
    set({ loading: true })
    try {
      const res = await fetch('/api/settings')
      if (res.ok) {
        const data = await res.json()
        set({ settings: data })
      }
    } catch {
      // defaults are fine
    } finally {
      set({ loading: false })
    }
  },

  toggleGate: async (gate) => {
    const current = get().settings[gate]
    set((state) => ({
      settings: { ...state.settings, [gate]: !current },
    }))
  },
}))
