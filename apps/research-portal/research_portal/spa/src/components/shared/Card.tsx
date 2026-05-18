import type { ReactNode } from 'react'

type CardVariant = 'default' | 'surface' | 'bordered'

const variantClasses: Record<CardVariant, string> = {
  default: 'bg-[#16213e] border border-[#2a2a4a]',
  surface: 'bg-[#1a1a2e] border border-[#2a2a4a]',
  bordered: 'bg-[#16213e] border-2 border-[#2a2a4a]',
}

interface CardProps {
  children: ReactNode
  className?: string
  onClick?: () => void
  variant?: CardVariant
  /** Subtle hover elevation — useful for clickable or dashboard cards */
  hover?: boolean
}

export function Card({ children, className = '', onClick, variant = 'default', hover }: CardProps) {
  return (
    <div
      className={`rounded-lg p-5 transition-all duration-200 ${variantClasses[variant]} ${
        onClick ? 'cursor-pointer' : ''
      } ${
        hover
          ? 'hover:shadow-lg hover:shadow-[#e94560]/5 hover:-translate-y-0.5 hover:border-[#e94560]/30'
          : onClick
            ? 'hover:border-[#e94560]'
            : ''
      } ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  )
}
