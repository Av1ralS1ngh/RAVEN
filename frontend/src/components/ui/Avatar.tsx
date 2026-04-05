import clsx from 'clsx'

type AvatarSize = 'sm' | 'md' | 'lg'

interface AvatarProps {
  name: string
  size?: AvatarSize
  colorIndex?: number
}

const sizeClasses: Record<AvatarSize, string> = {
  sm: 'w-6 h-6 text-[10px]',
  md: 'w-8 h-8 text-xs',
  lg: 'w-10 h-10 text-sm',
}

// 4 bg/text combos cycling through accent palette at 20% opacity
const colorVariants = [
  { bg: 'bg-[#A855F7]/20', text: 'text-[#DDB7FF]' }, // purple
  { bg: 'bg-[#1D9E75]/20', text: 'text-[#1D9E75]' }, // teal
  { bg: 'bg-blue-500/20',  text: 'text-blue-300'  }, // blue
  { bg: 'bg-[#639922]/20', text: 'text-[#639922]' }, // green
]

function getInitials(name: string): string {
  const words = name.trim().split(/\s+/)
  const first = words[0]?.[0] ?? ''
  const last  = words.length > 1 ? (words[words.length - 1]?.[0] ?? '') : ''
  return (first + last).toUpperCase()
}

export default function Avatar({ name, size = 'md', colorIndex }: AvatarProps) {
  // Derive a stable color from the name if no colorIndex provided
  const index =
    colorIndex !== undefined
      ? colorIndex % 4
      : name.charCodeAt(0) % 4

  const { bg, text } = colorVariants[index]
  const initials = getInitials(name)

  return (
    <div
          title={name}
      className={clsx(
        'inline-flex items-center justify-center rounded-full font-mono font-medium select-none shrink-0',
        sizeClasses[size],
        bg,
        text,
      )}
    >
      {initials}
    </div>
  )
}
