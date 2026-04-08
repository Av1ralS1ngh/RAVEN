import { useEffect, useMemo, useRef, useState } from 'react'
import * as d3 from 'd3'
import type { DiscoveryGraph, DiscoveryNode } from '@/types/discovery.types'

interface PositionedNode extends DiscoveryNode {
  x: number
  y: number
}

interface PositionedEdge {
  id: string
  source: PositionedNode
  target: PositionedNode
  edgeType: string
  weight: number
}

interface TooltipState {
  node: PositionedNode
  x: number
  y: number
}

interface SkillGraphNetworkProps {
  graph: DiscoveryGraph | null
  isLoading?: boolean
}

const MAX_RENDER_NODES = 120
const MAX_RENDER_EDGES = 320

function edgeColor(edgeType: string): string {
  if (edgeType === 'ROLE_REQUIRES_SKILL' || edgeType === 'ROLE_USES_LIB' || edgeType === 'ROLE_IN_DOMAIN') {
    return '#93c5fd'
  }
  if (edgeType === 'SKILL_RELATES_TO_SKILL' || edgeType === 'SKILL_IN_DOMAIN' || edgeType === 'SKILL_USES_LIB') {
    return '#86efac'
  }
  if (edgeType === 'TRAIT_ALIGNS_ROLE' || edgeType === 'TRAIT_RELATES_TO_SKILL') {
    return '#f9a8d4'
  }
  if (edgeType === 'RESOURCE_TEACHES_SKILL' || edgeType === 'RESOURCE_IN_DOMAIN') {
    return '#fef08a'
  }
  if (edgeType === 'IMPORTS' || edgeType === 'CALLS' || edgeType === 'FILE_SUPPORTS_SKILL') {
    return '#fdba74'
  }
  if (edgeType === 'DOMAIN_RELATES_TO_DOMAIN') {
    return '#c4b5fd'
  }
  return '#9db3ca'
}

function stableHash(value: string): number {
  let hash = 0
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 31 + value.charCodeAt(i)) >>> 0
  }
  return hash
}

function nodeColor(node: PositionedNode): string {
  if (node.node_type === 'RoleNode') {
    return '#c6d8ec'
  }
  if (node.node_type === 'SkillNode') {
    if (node.category === 'language') {
      return '#93c5fd'
    }
    if (node.category === 'framework') {
      return '#a7f3d0'
    }
    if (node.category === 'database') {
      return '#f3bd7a'
    }
    if (node.category === 'platform') {
      return '#c4b5fd'
    }
    return '#9db3ca'
  }
  if (node.node_type === 'TraitNode') {
    return '#f9a8d4'
  }
  if (node.node_type === 'DomainNode') {
    return '#fef08a'
  }
  if (node.node_type === 'LearningResourceNode') {
    return '#86efac'
  }
  if (node.node_type === 'FileNode') {
    return '#fdba74'
  }
  return '#cbd5e1'
}

function nodeRadius(node: PositionedNode): number {
  if (node.node_type === 'RoleNode') {
    return 22
  }
  if (node.node_type === 'SkillNode') {
    return 12 + Math.round(node.score * 5)
  }
  if (node.node_type === 'DomainNode') {
    return 14
  }
  if (node.node_type === 'TraitNode') {
    return 11
  }
  if (node.node_type === 'FileNode') {
    return 9
  }
  return 10
}

function shouldRenderInlineLabel(node: PositionedNode): boolean {
  // Dense graph mode: keep node labels tooltip-only for readability.
  void node
  return false
}

export default function SkillGraphNetwork({ graph, isLoading = false }: SkillGraphNetworkProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const viewportRef = useRef<SVGGElement>(null)
  const wrapperRef = useRef<HTMLDivElement>(null)
  const [tooltip, setTooltip] = useState<TooltipState | null>(null)

  const layout = useMemo(() => {
    if (!graph || graph.nodes.length === 0) {
      return { nodes: [] as PositionedNode[], edges: [] as PositionedEdge[] }
    }

    const width = 900
    const height = 380

    const prioritizedNodes = [...graph.nodes]
      .sort((a, b) => {
        const aRole = a.node_type === 'RoleNode' ? 1 : 0
        const bRole = b.node_type === 'RoleNode' ? 1 : 0
        const aSkill = a.node_type === 'SkillNode' ? 1 : 0
        const bSkill = b.node_type === 'SkillNode' ? 1 : 0
        if (aRole !== bRole) {
          return bRole - aRole
        }
        if (aSkill !== bSkill) {
          return bSkill - aSkill
        }
        if (a.score !== b.score) {
          return b.score - a.score
        }
        return a.label.localeCompare(b.label)
      })
      .slice(0, MAX_RENDER_NODES)

    const allowedNodeKeys = new Set(
      prioritizedNodes.map(node => `${node.node_type}|${node.id}`),
    )

    const prioritizedEdges = graph.edges
      .filter(edge => {
        const srcKey = `${edge.src_type}|${edge.src_id}`
        const tgtKey = `${edge.tgt_type}|${edge.tgt_id}`
        return allowedNodeKeys.has(srcKey) && allowedNodeKeys.has(tgtKey)
      })
      .sort((a, b) => b.weight - a.weight)
      .slice(0, MAX_RENDER_EDGES)

    const nodes: PositionedNode[] = prioritizedNodes.map((node, index) => {
      const seed = stableHash(`${node.id}:${node.node_type}:${index}`)
      return {
        ...node,
        x: 80 + (seed % 740),
        y: 60 + ((seed >> 4) % 260),
      }
    })

    const nodeIndex = new Map(nodes.map(node => [`${node.node_type}|${node.id}`, node]))

    const edges: PositionedEdge[] = []
    for (const edge of prioritizedEdges) {
      const source = nodeIndex.get(`${edge.src_type}|${edge.src_id}`)
      const target = nodeIndex.get(`${edge.tgt_type}|${edge.tgt_id}`)
      if (!source || !target) {
        continue
      }
      edges.push({
        id: `${edge.edge_type}:${edge.src_id}:${edge.tgt_id}`,
        source,
        target,
        edgeType: edge.edge_type,
        weight: edge.weight,
      })
    }

    const simulation = d3
      .forceSimulation(nodes)
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('charge', d3.forceManyBody().strength(-180))
      .force(
        'link',
        d3
          .forceLink(edges)
          .id(node => (node as PositionedNode).id)
          .distance(link => 95 - Math.round((link as PositionedEdge).weight * 28))
          .strength(0.15),
      )
      .force('collision', d3.forceCollide<PositionedNode>(node => nodeRadius(node) + 5).iterations(2))
      .stop()

    for (let i = 0; i < 240; i += 1) {
      simulation.tick()
    }

    return { nodes, edges }
  }, [graph])

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
      .scaleExtent([0.55, 2.8])
      .translateExtent([
        [-160, -120],
        [1060, 540],
      ])
      .on('zoom', event => {
        viewportSelection.attr('transform', event.transform.toString())
      })

    selection.call(zoom)

    return () => {
      selection.on('.zoom', null)
    }
  }, [layout.nodes.length, layout.edges.length])

  if (isLoading) {
    return (
      <div className="rounded-lg border border-[#2b3440] bg-[#0b1118] h-[360px] flex items-center justify-center">
        <p className="text-[#9aa6b4] text-sm">Synthesizing discovery graph...</p>
      </div>
    )
  }

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="rounded-lg border border-[#2b3440] bg-[#0b1118] h-[360px] flex items-center justify-center px-4 text-center">
        <p className="text-[#7f8c9a] text-sm">Complete the quiz to generate a TigerGraph-powered discovery network.</p>
      </div>
    )
  }

  const handleMove = (event: React.MouseEvent<SVGCircleElement>, node: PositionedNode) => {
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

  return (
    <div ref={wrapperRef} className="relative rounded-lg border border-[#2b3440] bg-[#0b1118] p-2">
      <svg
        ref={svgRef}
        viewBox="0 0 900 380"
        className="w-full h-[360px]"
        role="img"
        aria-label="Skill discovery network graph"
      >
        <g ref={viewportRef}>
          {layout.edges.map(edge => (
            <line
              key={edge.id}
              x1={edge.source.x}
              y1={edge.source.y}
              x2={edge.target.x}
              y2={edge.target.y}
              stroke={edgeColor(edge.edgeType)}
              strokeOpacity={0.22 + edge.weight * 0.38}
              strokeWidth={0.8 + edge.weight * 1.8}
            />
          ))}

          {layout.nodes.map(node => (
            <g key={`${node.node_type}:${node.id}`}>
              <circle
                cx={node.x}
                cy={node.y}
                r={nodeRadius(node)}
                fill={nodeColor(node)}
                fillOpacity={0.82}
                stroke="#e8eff7"
                strokeOpacity={0.42}
                strokeWidth={1}
                onMouseMove={event => handleMove(event, node)}
                onMouseLeave={() => setTooltip(null)}
              />
              {shouldRenderInlineLabel(node) && (
                <text
                  x={node.x}
                  y={node.y + 4}
                  textAnchor="middle"
                  className="select-none"
                  style={{
                    fill: '#091019',
                    fontSize: 8,
                    fontWeight: 700,
                    letterSpacing: '0.02em',
                  }}
                >
                  {node.label.length > 12 ? `${node.label.slice(0, 11)}…` : node.label}
                </text>
              )}
            </g>
          ))}
        </g>
      </svg>

      <div className="mt-2 flex items-center justify-between gap-3 px-1 text-[10px] text-[#7f8c9a] uppercase tracking-[0.14em]">
        <span>Pan and zoom to inspect connected recommendations</span>
        <span>{layout.nodes.length}/{graph.node_count} nodes • {layout.edges.length}/{graph.edge_count} edges</span>
      </div>

      {tooltip && (
        <div
          className="absolute pointer-events-none z-20 rounded-md border border-[#2b3440] bg-[#121a24] px-2.5 py-1.5 shadow-[0_8px_24px_rgba(0,0,0,0.35)]"
          style={{ left: tooltip.x, top: tooltip.y }}
        >
          <div className="text-[#e8eff7] text-xs font-label">{tooltip.node.label}</div>
          <div className="text-[#9db3ca] text-[10px] uppercase tracking-[0.08em] mt-0.5">{tooltip.node.node_type}</div>
          <div className="text-[#7f8c9a] text-[10px] uppercase tracking-[0.08em] mt-0.5">{tooltip.node.category}</div>
        </div>
      )}
    </div>
  )
}
