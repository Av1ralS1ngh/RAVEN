import Badge from '@/components/ui/Badge'
import type { DepBlastEntry, Severity } from '@/types/blast.types'

interface DepBlastTableProps {
  entries: DepBlastEntry[]
  selectedLib: string | null
  onSelect: (lib: string) => void
}

const severityVariant: Record<Severity, 'red' | 'amber' | 'green'> = {
  high:   'red',
  medium: 'amber',
  low:    'green',
}

export default function DepBlastTable({ entries, selectedLib, onSelect }: DepBlastTableProps) {
  if (!entries || entries.length === 0) {
    return (
      <div className="flex items-center justify-center py-8">
        <p className="text-sm text-[#666666]">No dependencies found.</p>
      </div>
    )
  }

  return (
    <div className="max-h-80 overflow-y-auto scrollbar-thin scrollbar-track-transparent scrollbar-thumb-white/10">
      {entries.map(entry => {
        const isSelected = entry.lib_name === selectedLib
        return (
          <div
            key={entry.lib_name}
            onClick={() => onSelect(entry.lib_name)}
            className={[
              'flex items-center justify-between px-3 py-2.5 cursor-pointer transition-colors duration-100',
              isSelected
                ? 'bg-[#393939] border-l-2 border-[#A855F7]'
                : 'border-l-2 border-transparent hover:bg-white/[0.03]',
            ].join(' ')}
          >
            <span className="font-mono text-sm text-[#E2E2E2] truncate mr-3">{entry.lib_name}</span>
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-xs text-[#666666] tabular-nums">{entry.affected_count} files</span>
              <Badge variant={severityVariant[entry.severity]} size="sm">
                {entry.severity}
              </Badge>
            </div>
          </div>
        )
      })}
    </div>
  )
}
