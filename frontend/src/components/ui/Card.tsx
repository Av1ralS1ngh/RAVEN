import clsx from 'clsx'
import type { ReactNode } from 'react'

interface CardProps {
  title?: string
  subtitle?: string
  className?: string
  children: ReactNode
  action?: ReactNode
}

export default function Card({
  title,
  subtitle,
  className,
  children,
  action,
}: CardProps) {
  return (
    <div
      className={clsx(
        'bg-surface-container border border-white/10 rounded-none p-4',
        className,
      )}
    >
      {(title || action) && (
        <div className="flex justify-between items-start mb-3">
          <div className="flex flex-col gap-0.5">
            {title && (
              <h3 className="text-xs font-medium text-[#CFC2D6] uppercase tracking-wide font-mono">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-xs text-[#666666]">{subtitle}</p>
            )}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </div>
      )}
      {children}
    </div>
  )
}
