import type { ReactNode } from 'react'

type BadgeVariant = 'green' | 'yellow' | 'red' | 'blue' | 'gray'

const variantClasses: Record<BadgeVariant, string> = {
  green: 'bg-green-900/40 text-green-300 border-green-700',
  yellow: 'bg-yellow-900/40 text-yellow-300 border-yellow-700',
  red: 'bg-red-900/40 text-red-300 border-red-700',
  blue: 'bg-blue-900/40 text-blue-300 border-blue-700',
  gray: 'bg-gray-700/40 text-gray-300 border-gray-600',
}

const dotClasses: Record<BadgeVariant, string> = {
  green: 'bg-green-400',
  yellow: 'bg-yellow-400',
  red: 'bg-red-400',
  blue: 'bg-blue-400',
  gray: 'bg-gray-400',
}

interface BadgeProps {
  children: ReactNode
  variant?: BadgeVariant
  /** Show colored dot instead of full pill — cleaner for inline status indicators */
  dot?: boolean
}

export function Badge({ children, variant = 'gray', dot }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 ${
        dot
          ? 'text-xs text-[#8888aa]'
          : 'inline-block px-2 py-0.5 rounded-full text-xs font-semibold border'
      } ${dot ? '' : variantClasses[variant]}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotClasses[variant]}`} />}
      {children}
    </span>
  )
}
