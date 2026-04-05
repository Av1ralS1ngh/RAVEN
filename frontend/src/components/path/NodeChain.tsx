import { ChevronRight } from 'lucide-react'
import Avatar from '@/components/ui/Avatar'
import Badge from '@/components/ui/Badge'
import type { PersonSummary } from '@/types/path.types'

interface NodeChainProps {
  path: PersonSummary[]
  variant?: 'primary' | 'secondary'
}

const RING_COLORS = {
  you:      'ring-2 ring-[#A855F7]',
  bridge:   'ring-2 ring-blue-500/50',
  recruiter:'ring-2 ring-[#1D9E75]',
}

function truncate(str: string, max: number): string {
  return str.length > max ? str.slice(0, max) + '…' : str
}

function NodeChip({
  person,
  ringClass,
  small,
}: {
  person: PersonSummary
  ringClass: string
  small: boolean
}) {
  return (
    <div
      className={`flex flex-col items-center gap-1 shrink-0 ${small ? 'opacity-60' : ''}`}
    >
      <div className={`rounded-full ${ringClass} ring-offset-2 ring-offset-[#131313]`}>
        <Avatar name={person.name} size={small ? 'sm' : 'md'} />
      </div>
      <span
        className={`text-center font-medium text-[#E2E2E2] leading-tight ${
          small ? 'text-[10px]' : 'text-xs'
        }`}
      >
        {truncate(person.name, 12)}
      </span>
      {person.company && (
        <span
          className={`text-center text-[#CFC2D6] leading-tight ${
            small ? 'text-[10px]' : 'text-xs'
          }`}
        >
          {truncate(person.company, 10)}
        </span>
      )}
    </div>
  )
}

/**
 * Horizontal node chain: You → Bridge Node(s) → Recruiter.
 * Horizontally scrollable, hidden scrollbar.
 */
export default function NodeChain({ path, variant = 'primary' }: NodeChainProps) {
  if (!path.length) return null

  const small = variant === 'secondary'
  const hops = path.length - 1

  function getRingClass(index: number): string {
    if (index === 0) return RING_COLORS.you
    if (index === path.length - 1) return RING_COLORS.recruiter
    return RING_COLORS.bridge
  }

  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">
      {path.map((person, i) => (
        <div key={person.id || i} className="flex items-center gap-2">
          <NodeChip
            person={person}
            ringClass={getRingClass(i)}
            small={small}
          />
          {i < path.length - 1 && (
            <ChevronRight
              size={small ? 12 : 14}
              className="text-[#666666] shrink-0 mt-[-12px]"
            />
          )}
        </div>
      ))}

      {/* Hop count badge */}
      <Badge variant="amber" size="sm" className="ml-3 shrink-0 self-start mt-1">
        {hops} {hops === 1 ? 'hop' : 'hops'}
      </Badge>
    </div>
  )
}
