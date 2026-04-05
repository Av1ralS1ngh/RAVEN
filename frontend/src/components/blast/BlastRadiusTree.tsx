import { useEffect, useRef, useMemo } from 'react'
import * as d3 from 'd3'
import type { FileImpactEntry } from '@/types/blast.types'

interface BlastRadiusTreeProps {
  impacts: FileImpactEntry[]
  libName: string
}

const DEPTH_COLORS: Record<number, string> = {
  1: '#FF4444',
  2: '#FFAA00',
  3: '#44BB66',
}

function depthColor(d: number): string {
  return DEPTH_COLORS[d] ?? DEPTH_COLORS[3]
}

function shortPath(path: string): string {
  const segs = path.replace(/\\/g, '/').split('/')
  return segs.slice(-3).join('/')
}

export default function BlastRadiusTree({ impacts, libName: _libName }: BlastRadiusTreeProps) {
  const chartRef = useRef<SVGSVGElement>(null)

  // Group by depth
  const grouped = useMemo(() => {
    const map = new Map<number, FileImpactEntry[]>()
    for (const item of impacts) {
      const d = item.depth >= 3 ? 3 : item.depth
      if (!map.has(d)) map.set(d, [])
      map.get(d)!.push(item)
    }
    return [...map.entries()].sort(([a], [b]) => a - b)
  }, [impacts])

  // D3 bar chart
  useEffect(() => {
    const svg = chartRef.current
    if (!svg || grouped.length === 0) return

    const width = svg.clientWidth || 300
    const height = 80
    const padding = { l: 8, r: 8, t: 16, b: 4 }
    const innerW = width - padding.l - padding.r
    const innerH = height - padding.t - padding.b

    d3.select(svg).selectAll('*').remove()

    const data = grouped.map(([depth, items]) => ({ depth, count: items.length }))

    const xScale = d3
      .scaleBand()
      .domain(data.map(d => String(d.depth)))
      .range([0, innerW])
      .padding(0.35)

    const maxCount = d3.max(data, d => d.count) ?? 1
    const yScale = d3.scaleLinear().domain([0, maxCount]).range([innerH, 0])

    const g = d3
      .select(svg)
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${padding.l},${padding.t})`)

    // Bars
    g.selectAll('rect')
      .data(data)
      .join('rect')
      .attr('x', d => xScale(String(d.depth))!)
      .attr('y', d => yScale(d.count))
      .attr('width', xScale.bandwidth())
      .attr('height', d => innerH - yScale(d.count))
      .attr('fill', d => depthColor(d.depth) + 'B3')  // 70% opacity
      .attr('rx', 2)

    // Count labels above bars
    g.selectAll('text')
      .data(data)
      .join('text')
      .attr('x', d => xScale(String(d.depth))! + xScale.bandwidth() / 2)
      .attr('y', d => yScale(d.count) - 4)
      .attr('text-anchor', 'middle')
      .attr('font-size', 10)
      .attr('font-family', 'monospace')
      .attr('fill', d => depthColor(d.depth))
      .text(d => d.count)
  }, [grouped])

  if (!impacts || impacts.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-sm text-[#666666]">Select a library to see blast radius</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {/* File list grouped by depth */}
      {grouped.map(([depth, files]) => (
        <div key={depth}>
          <div className="flex items-center gap-2 mb-1.5">
            <span
              className="w-1.5 h-1.5 rounded-full shrink-0"
              style={{ background: depthColor(depth) }}
            />
            <span className="text-[10px] font-mono text-[#666666] uppercase tracking-widest">
              Depth {depth}{depth >= 3 ? '+' : ''}
            </span>
          </div>
          <div className="flex flex-col gap-0.5 pl-3.5">
            {files.map((f, i) => (
              <div key={i} className="flex items-center justify-between gap-2 py-0.5">
                <div className="flex items-center gap-2 min-w-0">
                  <span
                    className="w-1.5 h-1.5 rounded-full shrink-0"
                    style={{ background: depthColor(depth) }}
                  />
                  <span className="font-mono text-xs text-[#E2E2E2] truncate">
                    {shortPath(f.path)}
                  </span>
                </div>
                <span className="text-xs text-[#666666] shrink-0">{f.repo}</span>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* D3 bar chart */}
      {grouped.length > 0 && (
        <div className="mt-2 pt-3 border-t border-white/5">
          <p className="text-[10px] text-[#666666] uppercase tracking-widest font-mono mb-2">
            Files per depth
          </p>
          <svg ref={chartRef} className="w-full" style={{ height: 80 }} />
        </div>
      )}
    </div>
  )
}
