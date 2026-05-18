import { create } from 'zustand'

export type ToastVariant = 'success' | 'error' | 'info'

export interface Toast {
  id: string
  message: string
  variant: ToastVariant
}

interface ToastState {
  toasts: Toast[]
  addToast: (message: string, variant: ToastVariant) => void
  dismissToast: (id: string) => void
}

let nextId = 0
function genId(): string {
  return `toast-${++nextId}-${Date.now()}`
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  addToast: (message, variant) => {
    const id = genId()
    set((state) => ({
      toasts: [...state.toasts, { id, message, variant }],
    }))
    // Auto-dismiss after 4 seconds
    setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((t) => t.id !== id),
      }))
    }, 4000)
  },
  dismissToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }))
  },
}))
