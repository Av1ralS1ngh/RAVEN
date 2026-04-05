import clsx from 'clsx'
import type { InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
}

export default function Input({
  label,
  error,
  hint,
  id,
  className,
  ...rest
}: InputProps) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-')

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label
          htmlFor={inputId}
          className="text-xs text-[#CFC2D6] uppercase tracking-wide font-mono"
        >
          {label}
        </label>
      )}

      <input
        {...rest}
        id={inputId}
        className={clsx(
          'w-full bg-black border rounded-none px-3 py-2 text-sm text-[#E2E2E2]',
          'placeholder:text-[#666666]',
          'focus:outline-none focus:ring-1 focus:ring-[#DDB7FF]/50',
          'transition-colors duration-100',
          error
            ? 'border-[#FF4444]'
            : 'border-[#222222] hover:border-[#4D4354]',
          className,
        )}
      />

      {hint && !error && (
        <p className="text-xs text-[#666666]">{hint}</p>
      )}

      {error && (
        <p className="text-xs text-red-400" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
