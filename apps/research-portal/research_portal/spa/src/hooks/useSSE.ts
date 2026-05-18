import { useEffect, useRef, useCallback } from 'react'
import type { SSEEvent } from '../types'

interface UseSSEOptions {
  onEvent: (event: SSEEvent) => void
  onError?: (error: Event) => void
  onComplete?: () => void
}

export function useSSE(url: string | null, options: UseSSEOptions) {
  const eventSourceRef = useRef<EventSource | null>(null)
  const optionsRef = useRef(options)
  optionsRef.current = options

  const close = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!url) return

    close()

    const es = new EventSource(url)
    eventSourceRef.current = es

    const eventTypes = ['thinking', 'action', 'result', 'done', 'error']

    eventTypes.forEach((type) => {
      es.addEventListener(type, (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data)
          optionsRef.current.onEvent({ event: type as SSEEvent['event'], data })
        } catch {
          optionsRef.current.onEvent({ event: type as SSEEvent['event'], data: { raw: event.data } })
        }
      })
    })

    es.onerror = (event) => {
      optionsRef.current.onError?.(event)
      close()
    }

    return () => {
      close()
    }
  }, [url, close])

  return { close }
}
