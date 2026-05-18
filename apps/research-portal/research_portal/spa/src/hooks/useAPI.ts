import { useState, useCallback } from 'react'

interface UseAPIOptions {
  baseUrl?: string
}

export function useAPI(options: UseAPIOptions = {}) {
  const baseUrl = options.baseUrl || '/api/v1'
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAPI = useCallback(
    async <T>(url: string, init?: RequestInit): Promise<T> => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`${baseUrl}${url}`, {
          headers: { 'Content-Type': 'application/json' },
          ...init,
        })
        if (!res.ok) {
          const err = await res.text()
          throw new Error(err || `HTTP ${res.status}`)
        }
        return res.json()
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'Unknown error'
        setError(msg)
        throw e
      } finally {
        setLoading(false)
      }
    },
    [baseUrl]
  )

  return { fetchAPI, loading, error }
}
