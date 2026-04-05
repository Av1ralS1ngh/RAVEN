import clsx from 'clsx'

interface SkeletonProps {
  width?: string | number
  height?: string | number
  rounded?: boolean
  className?: string
}

export function Skeleton({ width, height, rounded = true, className }: SkeletonProps) {
  return (
    <div
      className={clsx(
        'bg-white/5 animate-pulse',
        rounded && 'rounded-md',
        className
      )}
      style={{ width, height }}
      aria-hidden="true"
    />
  )
}

export function SkeletonText({ width = '100%', className }: Omit<SkeletonProps, 'height'>) {
  return <Skeleton width={width} height="12px" className={className} />
}

export function SkeletonCard({ height = '120px', className }: Omit<SkeletonProps, 'width'>) {
  return <Skeleton width="100%" height={height} className={className} />
}
