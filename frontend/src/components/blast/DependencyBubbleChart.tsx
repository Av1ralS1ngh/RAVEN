import { useEffect, useMemo, useRef, useState } from 'react'
import * as d3 from 'd3'
import type { DepBlastEntry } from '@/types/blast.types'

interface BubbleNode extends DepBlastEntry {
  x: number
  y: number
  radius: number
}

interface TooltipState {
  node: BubbleNode
  x: number
  y: number
}

interface DependencyBubbleChartProps {
  deps: DepBlastEntry[]
  selectedLib: string | null
  onSelect: (libName: string) => void
  width?: number
  height?: number
}

function stableHash(value: string): number {
  let hash = 0
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 31 + value.charCodeAt(i)) >>> 0
  }
  return hash
}

function severityColor(severity: DepBlastEntry['severity']): string {
  if (severity === 'high') {
    return '#ff8b7d'
  }
  if (severity === 'medium') {
    return '#f3bd7a'
  }
  return '#9db3ca'
}

function radiusFor(dep: DepBlastEntry): number {
  // Guarantees low < medium < high while still reflecting affected_count.
  const boundedCount = Math.min(dep.affected_count, 60)
  if (dep.severity === 'high') {
    return 32 + Math.min(18, boundedCount * 0.35)
  }
  if (dep.severity === 'medium') {
    return 22 + Math.min(12, boundedCount * 0.25)
  }
  return 14 + Math.min(8, boundedCount * 0.15)
}

export default function DependencyBubbleChart({
  deps,
  selectedLib,
  onSelect,
  width = 720,
  height = 300,
}: DependencyBubbleChartProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const viewportRef = useRef<SVGGElement>(null)
  const wrapperRef = useRef<HTMLDivElement>(null)
  const [tooltip, setTooltip] = useState<TooltipState | null>(null)

  const nodes = useMemo(() => {
    if (deps.length === 0) {
      return []
    }

    const seeded = deps.map((dep, index) => {
      const seed = stableHash(`${dep.lib_name}:${index}`)
      return {
        ...dep,
        x: 90 + (seed % Math.max(1, width - 180)),
        y: 70 + ((seed >> 6) % Math.max(1, height - 140)),
        radius: radiusFor(dep),
      }
    })

    const sim = d3
      .forceSimulation<BubbleNode>(seeded)
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('x', d3.forceX(width / 2).strength(0.06))
      .force('y', d3.forceY(height / 2).strength(0.06))
      .force('collision', d3.forceCollide<BubbleNode>(node => node.radius + 3).iterations(2))
      .stop()

    for (let i = 0; i < 220; i += 1) {
      sim.tick()
    }

    return seeded
  }, [deps, width, height])

  useEffect(() => {
    const svg = svgRef.current
    const viewport = viewportRef.current
    if (!svg || !viewport) {
      return
    }

    const selection = d3.select(svg)
    const viewportSelection = d3.select(viewport)

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.65, 2.8])
      .translateExtent([
        [-140, -120],
        [width + 140, height + 120],
      ])
      .on('zoom', event => {
        viewportSelection.attr('transform', event.transform.toString())
      })

    selection.call(zoom)

    return () => {
      selection.on('.zoom', null)
    }
  }, [width, height, nodes])

  const handleMove = (event: React.MouseEvent<SVGCircleElement>, node: BubbleNode) => {
    const rect = wrapperRef.current?.getBoundingClientRect()
    if (!rect) {
      return
    }

    setTooltip({
      node,
      x: event.clientX - rect.left + 12,
      y: event.clientY - rect.top + 12,
    })
  }

  if (deps.length === 0) {
    return (
      <div className="rounded-lg border border-[#2b3440] bg-[#0b1118] h-[280px] flex items-center justify-center">
        <p className="text-[#7f8c9a] text-xs">No dependencies for this filter.</p>
      </div>
    )
  }

  return (
    <div ref={wrapperRef} className="relative rounded-lg border border-[#2b3440] bg-[#0b1118] p-2">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-[280px]"
        role="img"
        aria-label="Dependency blast bubble chart"
      >
        <g ref={viewportRef}>
          {nodes.map(node => {
            const selected = node.lib_name === selectedLib
            return (
              <g key={node.lib_name}>
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={node.radius}
                  fill={severityColor(node.severity)}
                  fillOpacity={selected ? 0.52 : 0.36}
                  stroke={selected ? '#e7eff8' : '#9fb5cb'}
                  strokeOpacity={selected ? 0.95 : 0.45}
                  strokeWidth={selected ? 2.2 : 1}
                  className="cursor-pointer transition-all"
                  onClick={() => onSelect(node.lib_name)}
                  onMouseMove={event => handleMove(event, node)}
                  onMouseLeave={() => setTooltip(null)}
                />
              </g>
            )
          })}
        </g>
      </svg>

      <div className="mt-2 flex items-center justify-between gap-3 px-1">
        <div className="text-[10px] text-[#7f8c9a] uppercase tracking-[0.14em]">Scroll/Pinch to zoom • Drag to pan</div>
        <div className="flex items-center gap-3 text-[10px]">
          <span className="inline-flex items-center gap-1 text-[#9db3ca]"><span className="w-2 h-2 rounded-full bg-[#9db3ca]" />Low</span>
          <span className="inline-flex items-center gap-1 text-[#f3bd7a]"><span className="w-2 h-2 rounded-full bg-[#f3bd7a]" />Medium</span>
          <span className="inline-flex items-center gap-1 text-[#ff8b7d]"><span className="w-2 h-2 rounded-full bg-[#ff8b7d]" />High</span>
        </div>
      </div>

      {tooltip && (
        <div
          className="absolute pointer-events-none z-20 rounded-md border border-[#2b3440] bg-[#121a24] px-2.5 py-1.5 shadow-[0_8px_24px_rgba(0,0,0,0.35)]"
          style={{ left: tooltip.x, top: tooltip.y }}
        >
          <div className="text-[#e8eff7] text-xs font-label">{tooltip.node.lib_name}</div>
        </div>
      )}
    </div>
  )
}
