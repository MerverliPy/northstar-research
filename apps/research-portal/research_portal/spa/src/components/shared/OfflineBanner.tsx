import { useState, useEffect } from 'react'
import { useToastStore } from '../../stores/toastStore'

export function OfflineBanner() {
  const [offline, setOffline] = useState(!navigator.onLine)
  const addToast = useToastStore((s) => s.addToast)

  useEffect(() => {
    function goOffline() { setOffline(true) }
    function goOnline() {
      setOffline(false)
      addToast('Back online', 'success')
    }

    window.addEventListener('offline', goOffline)
    window.addEventListener('online', goOnline)
    return () => {
      window.removeEventListener('offline', goOffline)
      window.removeEventListener('online', goOnline)
    }
  }, [addToast])

  if (!offline) return null

  return (
    <div
      className="fixed top-14 left-0 right-0 z-[200] bg-yellow-700/90 text-white text-center text-sm py-2 px-4
        flex items-center justify-center gap-2"
      role="alert"
    >
      <span className="w-2 h-2 rounded-full bg-yellow-300 inline-block animate-pulse" />
      You are offline — some features may be unavailable
    </div>
  )
}
