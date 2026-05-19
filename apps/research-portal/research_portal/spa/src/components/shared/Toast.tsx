import { useToastStore } from '../../stores/toastStore'
import type { ToastVariant } from '../../stores/toastStore'

const variantStyles: Record<ToastVariant, { bg: string; border: string; icon: string }> = {
  success: {
    bg: 'bg-green-900/80',
    border: 'border-green-700',
    icon: '✓',
  },
  error: {
    bg: 'bg-red-900/80',
    border: 'border-red-700',
    icon: '✕',
  },
  info: {
    bg: 'bg-blue-900/80',
    border: 'border-blue-700',
    icon: 'ℹ',
  },
}

export function ToastContainer() {
  const { toasts, dismissToast } = useToastStore()

  if (toasts.length === 0) return null

  return (
    <div
      className="fixed bottom-4 right-4 z-[100] flex flex-col-reverse gap-2 max-w-sm w-full pointer-events-none
        sm:items-end items-center"
      role="status"
      aria-live="polite"
      aria-label="Notifications"
    >
      {toasts.map((toast) => {
        const style = variantStyles[toast.variant]
        return (
          <div
            key={toast.id}
            className={`pointer-events-auto ${style.bg} border ${style.border} text-white rounded-lg px-4 py-3 shadow-lg flex items-center gap-3 animate-slide-in min-w-0`}
            style={{
              animation: 'slideIn 0.3s ease-out, fadeOut 0.3s ease-in 3.7s forwards',
            }}
          >
            <span
              className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold"
              style={{ background: 'rgba(255,255,255,0.15)' }}
            >
              {style.icon}
            </span>
            <span className="text-sm flex-1 truncate">{toast.message}</span>
            {toast.action && (
              <button
                onClick={() => { toast.action!.onClick(); dismissToast(toast.id) }}
                className="flex-shrink-0 bg-white/15 hover:bg-white/25 text-white rounded px-2 py-1 text-xs font-medium transition-colors"
              >
                {toast.action.label}
              </button>
            )}
            <button
              onClick={() => dismissToast(toast.id)}
              className="flex-shrink-0 text-white/60 hover:text-white ml-1 w-5 h-5 rounded flex items-center justify-center text-xs transition-colors"
              aria-label="Dismiss notification"
            >
              ×
            </button>
          </div>
        )
      })}
    </div>
  )
}
