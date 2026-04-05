import { Star } from 'lucide-react'
import type { TechCategory, TechItem } from '@/types/blast.types'

interface TechChipsProps {
  items: TechItem[]
  highlightTop?: number
}

const categoryVariant: Record<TechCategory, string> = {
  language:  'bg-[#1D9E75]/15 text-[#1D9E75] border border-[#1D9E75]/30',
  framework: 'bg-blue-500/15 text-blue-300 border border-blue-500/30',
  tool:      'bg-[#353535] text-[#CFC2D6] border border-white/10',
  platform:  'bg-[#FFAA00]/15 text-[#FFAA00] border border-[#FFAA00]/30',
  database:  'bg-[#44BB66]/15 text-[#44BB66] border border-[#44BB66]/30',
  other:     'bg-[#353535] text-[#CFC2D6] border border-white/10',
}

const topVariant = 'bg-[#A855F7]/20 text-[#DDB7FF] border border-[#A855F7]/30'

export default function TechChips({ items, highlightTop = 3 }: TechChipsProps) {
  if (!items || items.length === 0) {
    return <p className="text-xs text-[#666666]">No tech stack detected.</p>
  }

  // Sort descending by confidence; take top N
  const sorted = [...items].sort((a, b) => b.confidence - a.confidence)
  const topIds = new Set(sorted.slice(0, highlightTop).map(i => i.name))

  return (
    <div className="flex flex-wrap gap-1.5">
      {sorted.map(item => {
        const isTop = topIds.has(item.name)
        const cls = isTop ? topVariant : categoryVariant[item.category] ?? categoryVariant.other

        return (
          <span
            key={item.name}
            title={`Confidence: ${(item.confidence * 100).toFixed(0)}%`}
            className={[
              'inline-flex items-center gap-1 px-2 py-0.5 rounded-none text-[11px] font-mono tracking-wide font-medium select-none',
              cls,
            ].join(' ')}
          >
            {isTop && <Star size={10} className="shrink-0 fill-current" aria-hidden />}
            {item.name}
          </span>
        )
      })}
    </div>
  )
}
