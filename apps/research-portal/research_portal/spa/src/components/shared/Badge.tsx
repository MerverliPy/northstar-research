import type { ReactNode } from 'react'

type BadgeVariant = 'green' | 'yellow' | 'red' | 'blue' | 'gray'

const variantClasses: Record<BadgeVariant, string> = {
  green: 'bg-green-900/40 text-green-300 border-green-700',
  yellow: 'bg-yellow-900/40 text-yellow-300 border-yellow-700',
  red: 'bg-red-900/40 text-red-300 border-red-700',
  blue: 'bg-blue-900/40 text-blue-300 border-blue-700',
  gray: 'bg-gray-700/40 text-gray-300 border-gray-600',
}

interface BadgeProps {
  children: ReactNode
  variant?: BadgeVariant
}

export function Badge({ children, variant = 'gray' }: BadgeProps) {
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold border ${variantClasses[variant]}`}
    >
      {children}
    </span>
  )
}
