import { useCallback, useEffect, useRef } from 'react'
import { Workbox } from 'workbox-window'
import { useToastStore } from '../stores/toastStore'

export function usePWA() {
  const addToast = useToastStore((s) => s.addToast)
  const wbRef = useRef<Workbox | null>(null)

  const reloadWithUpdate = useCallback(() => {
    const wb = wbRef.current
    if (!wb) return
    wb.addEventListener('controlling', () => {
      window.location.reload()
    })
    wb.messageSkipWaiting()
  }, [])

  useEffect(() => {
    if (!('serviceWorker' in navigator)) return

    const wb = new Workbox('/sw.js')
    wbRef.current = wb

    wb.addEventListener('waiting', () => {
      addToast('Update available — reload for latest version', 'info', {
        label: 'Reload',
        onClick: reloadWithUpdate,
      })
    })

    wb.addEventListener('activated', () => {
      addToast('App updated successfully', 'success')
    })

    wb.register()

    return () => {
      wb.active?.then((worker) => worker?.postMessage?.({ type: 'SKIP_WAITING' }))
    }
  }, [addToast, reloadWithUpdate])
}
