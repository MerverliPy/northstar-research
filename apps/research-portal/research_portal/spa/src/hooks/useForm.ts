import { useState, useCallback } from 'react'

type Validator<T> = (value: T) => string | null

type Validators<T> = {
  [K in keyof T]?: Validator<T[K]>
}

type ErrorMap<T> = Partial<Record<keyof T, string>>

interface UseFormReturn<T> {
  form: T
  errors: ErrorMap<T>
  touched: Partial<Record<keyof T, boolean>>
  setField: <K extends keyof T>(field: K, value: T[K]) => void
  validateField: <K extends keyof T>(field: K) => string | null
  validateAll: () => boolean
  isValid: boolean
  resetForm: (initial: T) => void
}

export function useForm<T extends Record<string, unknown>>(
  initial: T,
  validators: Validators<T> = {}
): UseFormReturn<T> {
  const [form, setForm] = useState<T>(initial)
  const [errors, setErrors] = useState<ErrorMap<T>>({})
  const [touched, setTouched] = useState<Partial<Record<keyof T, boolean>>>({})

  const validateField = useCallback(
    <K extends keyof T>(field: K): string | null => {
      const validator = validators[field]
      if (!validator) return null
      return validator(form[field])
    },
    [form, validators]
  )

  const setField = useCallback(
    <K extends keyof T>(field: K, value: T[K]) => {
      setForm((prev) => ({ ...prev, [field]: value }))
      setTouched((prev) => ({ ...prev, [field]: true }))
      // Clear error on change
      setErrors((prev) => {
        const next = { ...prev }
        delete next[field]
        return next
      })
    },
    []
  )

  const validateAll = useCallback((): boolean => {
    const newErrors: ErrorMap<T> = {}
    const allTouched: Partial<Record<keyof T, boolean>> = {}
    for (const key of Object.keys(form) as Array<keyof T>) {
      const err = validateField(key)
      allTouched[key] = true
      if (err) newErrors[key] = err
    }
    setErrors(newErrors)
    setTouched(allTouched)
    return Object.keys(newErrors).length === 0
  }, [form, validateField])

  const isValid = Object.keys(errors).length === 0

  const resetForm = useCallback((newInitial: T) => {
    setForm(newInitial)
    setErrors({})
    setTouched({})
  }, [])

  return { form, errors, touched, setField, validateField, validateAll, isValid, resetForm }
}

// Common validators
export const required = (message = 'Required'): Validator<string> => {
  return (value: string) => (value.trim() ? null : message)
}

export const maxLength = (max: number, message?: string): Validator<string> => {
  return (value: string) =>
    value.length > max ? message || `Must be ${max} characters or less` : null
}

export const urlFormat = (message = 'Must be a valid URL'): Validator<string> => {
  return (value: string) => {
    if (!value) return null
    try {
      new URL(value)
      return null
    } catch {
      return message
    }
  }
}
