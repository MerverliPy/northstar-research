import { create } from 'zustand'

export type ToastVariant = 'success' | 'error' | 'info'

export interface ToastAction {
  label: string
  onClick: () => void
}

export interface Toast {
  id: string
  message: string
  variant: ToastVariant
  action?: ToastAction
}

interface ToastState {
  toasts: Toast[]
  addToast: (message: string, variant: ToastVariant, action?: ToastAction) => void
  dismissToast: (id: string) => void
}

let nextId = 0
function genId(): string {
  return `toast-${++nextId}-${Date.now()}`
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  addToast: (message, variant, action?) => {
    const id = genId()
    set((state) => ({
      toasts: [...state.toasts, { id, message, variant, action }],
    }))
    const timeout = action ? 8000 : 4000
    setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((t) => t.id !== id),
      }))
    }, timeout)
  },
  dismissToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }))
  },
}))
