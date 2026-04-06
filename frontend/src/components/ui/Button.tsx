import clsx from 'clsx'
import type { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  children: ReactNode
}

const sizeClasses = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
}

const variantClasses = {
  primary:
    'bg-accent-purple text-black font-medium hover:opacity-90 hover:border hover:border-matte-silver disabled:opacity-40',
  secondary:
    'bg-surface-container border border-white/10 text-[#E2E2E2] hover:bg-white/5 disabled:opacity-40',
  ghost:
    'bg-transparent text-[#CFC2D6] hover:text-[#E2E2E2] disabled:opacity-40',
}

/** Inline 16 × 16 spinner rendered when loading=true */
function Spinner() {
  return (
    <svg
      className="animate-spin"
      width={16}
      height={16}
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden
    >
      <circle
        cx="8"
        cy="8"
        r="6"
        stroke="currentColor"
        strokeOpacity="0.25"
        strokeWidth="2"
      />
      <path
        d="M14 8a6 6 0 0 0-6-6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  )
}

export default function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  children,
  className,
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      className={clsx(
        'btn-shine inline-flex items-center gap-2 rounded-none transition-all duration-100 cursor-pointer select-none',
        variantClasses[variant],
        sizeClasses[size],
        (disabled || loading) && 'cursor-not-allowed',
        className,
      )}
    >
      {loading && <Spinner />}
      {children}
    </button>
  )
}
