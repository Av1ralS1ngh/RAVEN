import Avatar from '@/components/ui/Avatar'
import Badge from '@/components/ui/Badge'
import type { PersonSummary } from '@/types/path.types'

interface BridgeNodesListProps {
  bridges: PersonSummary[]
}

type StrengthLevel = { label: string; variant: 'green' | 'blue' | 'gray' }

function getStrength(person: PersonSummary): StrengthLevel {
  if (person.mutual_count >= 10) return { label: 'Strong', variant: 'green' }
  if (person.mutual_count >= 4)  return { label: 'Medium', variant: 'blue'  }
  return                                { label: 'Weak',   variant: 'gray'  }
}

const MAX_VISIBLE = 5

/**
 * Vertical list of bridge nodes with a strength badge derived from the
 * person's id (stable, deterministic proxy for mutual_count).
 */
export default function BridgeNodesList({ bridges }: BridgeNodesListProps) {
  if (!bridges.length) {
    return (
      <p className="text-xs text-[#666666] py-2">No bridge nodes found.</p>
    )
  }

  const visible = bridges.slice(0, MAX_VISIBLE)
  const overflow = bridges.length - MAX_VISIBLE

  return (
    <div className="flex flex-col gap-3">
      {visible.map((person, i) => {
        const { label, variant } = getStrength(person)
        return (
          <div key={person.id || i} className="flex items-center gap-3">
            <Avatar name={person.name} size="sm" colorIndex={i + 1} />

            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-[#E2E2E2] truncate">
                {person.name}
              </p>
              {person.headline && (
                <p className="text-xs text-[#CFC2D6] truncate">
                  {person.headline}
                </p>
              )}
            </div>

            <Badge variant={variant} size="sm">
              {label}
            </Badge>
          </div>
        )
      })}

      {overflow > 0 && (
        <p className="text-xs text-[#666666] pt-1">+{overflow} more</p>
      )}
    </div>
  )
}
