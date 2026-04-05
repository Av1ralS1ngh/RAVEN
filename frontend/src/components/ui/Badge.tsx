import clsx from 'clsx'

type BadgeVariant = 'purple' | 'teal' | 'blue' | 'red' | 'amber' | 'green' | 'gray'
type BadgeSize = 'sm' | 'md'

interface BadgeProps {
  variant?: BadgeVariant
  size?: BadgeSize
  children: React.ReactNode
  className?: string
}

const variantClasses: Record<BadgeVariant, string> = {
  purple: 'bg-[#A855F7]/20 text-[#DDB7FF] border border-[#A855F7]/30',
  teal:   'bg-[#1D9E75]/20 text-[#1D9E75] border border-[#1D9E75]/30',
  blue:   'bg-blue-500/20  text-blue-300  border border-blue-500/30',
  red:    'bg-[#93000A]    text-[#FFB4AB] border border-[#FF4444]/30',
  amber:  'bg-[#FFAA00]/20 text-[#FFAA00] border border-[#FFAA00]/30',
  green:  'bg-[#44BB66]/20 text-[#44BB66] border border-[#44BB66]/30',
  gray:   'bg-[#353535]    text-[#CFC2D6] border border-white/10',
}

const sizeClasses: Record<BadgeSize, string> = {
  sm: 'px-2 py-0.5 text-[10px] font-mono tracking-wide',
  md: 'px-2.5 py-1 text-xs font-mono tracking-wide',
}

export default function Badge({
  variant = 'gray',
  size = 'sm',
  children,
  className,
}: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-none font-medium',
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
    >
      {children}
    </span>
  )
}
