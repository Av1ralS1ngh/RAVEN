interface StatsBarProps {
  hopCount: number
  totalConnections: number
  bridgeCount: number
}

interface MetricCardProps {
  value: number | string
  label: string
}

function MetricCard({ value, label }: MetricCardProps) {
  return (
    <div className="bg-[#131313] border border-white/10 p-4 text-center">
      <p className="text-3xl font-medium text-[#E2E2E2] font-mono tabular-nums">
        {value}
      </p>
      <p className="text-xs text-[#CFC2D6] mt-1 uppercase tracking-wide">
        {label}
      </p>
    </div>
  )
}

/**
 * Three key metrics displayed as a 3-column grid of stat cards.
 */
export default function StatsBar({ hopCount, totalConnections, bridgeCount }: StatsBarProps) {
  return (
    <div className="grid grid-cols-3 gap-4">
      <MetricCard value={hopCount} label="Hops" />
      <MetricCard
        value={totalConnections > 0 ? totalConnections.toLocaleString() : '—'}
        label="Connections"
      />
      <MetricCard value={bridgeCount} label="Bridge Nodes" />
    </div>
  )
}
