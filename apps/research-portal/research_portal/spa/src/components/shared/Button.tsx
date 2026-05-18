import type { ReactNode, ButtonHTMLAttributes } from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost'
type ButtonSize = 'sm' | 'md' | 'lg'

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'bg-[#e94560] text-white hover:bg-[#d63851] active:bg-[#c42e47]',
  secondary: 'bg-[#2a2a4a] text-[#e0e0e0] hover:bg-[#3a3a5a] active:bg-[#4a4a6a]',
  danger: 'bg-red-700 text-white hover:bg-red-600 active:bg-red-500',
  ghost: 'bg-transparent text-[#8888aa] hover:text-[#e0e0e0] hover:bg-[#2a2a4a] active:bg-[#3a3a5a]',
}

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'px-3 py-1 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  children: ReactNode
  /** Show loading spinner and disable button */
  loading?: boolean
  /** Icon-only mode — removes padding for icon buttons */
  icon?: boolean
}

function Spinner() {
  return (
    <svg
      className="animate-spin -ml-1 h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  )
}

export function Button({
  variant = 'primary',
  size = 'md',
  children,
  className = '',
  disabled,
  loading,
  icon,
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-md font-medium transition-all duration-150
        ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        ${variantClasses[variant]}
        ${icon ? 'p-1.5' : sizeClasses[size]}
        ${className}`}
      disabled={isDisabled}
      {...props}
    >
      {loading && <Spinner />}
      {children}
    </button>
  )
}
