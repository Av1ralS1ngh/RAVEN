import SkillQuiz from '@/components/dashboard/SkillQuiz'
import SkillGraphNetwork from '@/components/dashboard/SkillGraphNetwork'
import TopSkills from '@/components/dashboard/TopSkills'
import { useSkillDiscovery } from '@/hooks/useSkillDiscovery'
import { useEffect, useMemo } from 'react'
import { Sparkles, Compass, Globe } from 'lucide-react'

export default function WhatToChoosePage() {
  const {
    submitQuiz,
    loadTrending,
    isLoading,
    isLoadingTrending,
    error,
    warning,
    result,
    trending,
  } = useSkillDiscovery()

  useEffect(() => {
    void loadTrending(8)
  }, [loadTrending])

  const nodeTypeSummary = useMemo(() => {
    if (!result) {
      return [] as Array<[string, number]>
    }
    const counts = new Map<string, number>()
    for (const node of result.graph.nodes) {
      counts.set(node.node_type, (counts.get(node.node_type) ?? 0) + 1)
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1])
  }, [result])

  const edgeTypeSummary = useMemo(() => {
    if (!result) {
      return [] as Array<[string, number]>
    }
    const counts = new Map<string, number>()
    for (const edge of result.graph.edges) {
      counts.set(edge.edge_type, (counts.get(edge.edge_type) ?? 0) + 1)
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1])
  }, [result])

  return (
    <section className="flex-1 flex flex-col min-w-0 p-6 md:p-10 gap-10 bg-[radial-gradient(circle_at_0%_0%,#1a232e_0%,#090b0f_45%)]" data-purpose="discovery-interface">
      <header className="max-w-4xl">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-[#1a2431] rounded-lg border border-[#2b3440] icon-sheen-shell">
            <Globe className="w-6 h-6 icon-silver animate-pulse" />
          </div>
          <h2 className="text-[10px] font-label text-[#7d8793] uppercase tracking-[0.3em]">Global Discovery Protocol</h2>
        </div>
        <h1 className="text-4xl font-headline font-extrabold text-[#eef3f8] tracking-tight mb-4">Holistic Path Discovery</h1>
        <p className="text-[#9aa6b4] text-lg font-body max-w-2xl leading-relaxed">
          The future of tech isn't just about code. It's about strategy, design, and leadership. Our engine helps you discover where your unique strengths fit in the broader ecosystem.
        </p>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-10 items-start">
        <div className="space-y-6">
          <div className="flex items-center gap-2 mb-4 text-[#9db3ca]">
            <span className="p-1 rounded-md border border-[#2b3440] bg-[#0d1117] icon-sheen-shell"><Sparkles className="w-5 h-5 icon-silver" /></span>
            <h3 className="text-sm font-label uppercase tracking-widest">Interactive Pathway Quiz</h3>
          </div>
          <SkillQuiz onComplete={submitQuiz} isSubmitting={isLoading} />
        </div>
        
        <div className="space-y-6">
          <div className="flex items-center gap-2 mb-4 text-[#9db3ca]">
            <span className="p-1 rounded-md border border-[#2b3440] bg-[#0d1117] icon-sheen-shell"><Compass className="w-5 h-5 icon-silver" /></span>
            <h3 className="text-sm font-label uppercase tracking-widest">Trending Skill Clusters</h3>
          </div>
          <TopSkills trending={trending} isLoading={isLoadingTrending} />
        </div>
      </div>

      <section className="border border-[#2b3440] rounded-xl bg-[#0f141b]/95 p-6 md:p-8 space-y-4">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h3 className="text-sm font-label uppercase tracking-widest text-[#9db3ca]">Discovery Knowledge Graph</h3>
            <p className="text-[#7d8793] text-xs uppercase tracking-[0.18em] mt-2">
              TigerGraph-powered role, skill, trait, and resource relationships
            </p>
          </div>
          {result && (
            <div className="text-right">
              <p className="text-[#e6edf5] font-headline text-lg tracking-tight">{result.recommendation_title}</p>
              <p className="text-[#8ea0b3] text-xs uppercase tracking-[0.14em]">{result.query_time_ms.toFixed(0)} ms</p>
            </div>
          )}
        </div>

        {error && (
          <div className="rounded-lg border border-[#4f2f35] bg-[#1b1115] px-4 py-3 text-[#ffb4ab] text-sm">
            {error}
          </div>
        )}

        {warning && (
          <div className="rounded-lg border border-[#3d3525] bg-[#1a1710] px-4 py-3 text-[#f3bd7a] text-xs uppercase tracking-[0.1em]">
            {warning}
          </div>
        )}

        {result && (
          <p className="text-[#a7b6c6] text-sm leading-relaxed">{result.recommendation_desc}</p>
        )}

        <SkillGraphNetwork graph={result?.graph ?? null} isLoading={isLoading} />

        {result && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-2">
            <div className="rounded-lg border border-[#2b3440] bg-[#0d1219] p-3">
              <p className="text-[10px] uppercase tracking-[0.14em] text-[#8ea0b3] mb-2">Node Types In Graph</p>
              <div className="flex flex-wrap gap-2">
                {nodeTypeSummary.map(([name, count]) => (
                  <span key={name} className="px-2 py-1 rounded border border-[#2b3440] text-[10px] uppercase tracking-[0.08em] text-[#d8e3ee]">
                    {name} ({count})
                  </span>
                ))}
              </div>
            </div>
            <div className="rounded-lg border border-[#2b3440] bg-[#0d1219] p-3">
              <p className="text-[10px] uppercase tracking-[0.14em] text-[#8ea0b3] mb-2">Edge Types In Graph</p>
              <div className="flex flex-wrap gap-2">
                {edgeTypeSummary.slice(0, 12).map(([name, count]) => (
                  <span key={name} className="px-2 py-1 rounded border border-[#2b3440] text-[10px] uppercase tracking-[0.08em] text-[#d8e3ee]">
                    {name} ({count})
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {result && result.clusters.length > 0 && (
          <div className="flex flex-wrap gap-3 pt-2">
            {result.clusters.slice(0, 5).map(cluster => (
              <div key={cluster.category} className="px-3 py-2 rounded-md border border-[#2b3440] bg-[#111821]">
                <p className="text-[10px] uppercase tracking-[0.16em] text-[#8ea0b3] mb-1">{cluster.category}</p>
                <p className="text-xs text-[#d8e3ee]">{cluster.skills.slice(0, 3).join(' • ')}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      <footer className="mt-10 pt-10 border-t border-[#2b3440]/50">
        <p className="text-[#5f6b7a] text-xs font-mono uppercase tracking-[0.2em] text-center">
          Holistic Growth Engine &bull; System v3.1.0 &bull; Multi-disciplinary Mode
        </p>
      </footer>
    </section>
  )
}
