import { useCallback, useMemo } from 'react'
import { usePathFinder } from '@/hooks/usePathFinder'
import { Network } from 'lucide-react'

// Simple pseudo-random helper for stable bridge node labels.
const hashStr = (s: string) => s.split('').reduce((a, b) => { a = ((a << 5) - a) + b.charCodeAt(0); return a & a }, 0)

export default function PathFinderPage() {
  const {
    recruiterUrl, setRecruiterUrl,
    yourLinkedInId, setYourLinkedInId,
    isLoading, error, result,
    submit,
  } = usePathFinder()

  const handleKey = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading) submit()
  }, [isLoading, submit])

  const bridges = result ? result.path.slice(1, -1) : []
  const rankedAlternativePaths = useMemo(() => {
    if (!result) {
      return []
    }
    return [...result.alternative_paths].sort((a, b) => {
      if (a.length !== b.length) {
        return a.length - b.length
      }
      const aKey = a.map(node => node.id).join('>')
      const bKey = b.map(node => node.id).join('>')
      return aKey.localeCompare(bKey)
    })
  }, [result])

  return (
    <section className="flex-1 flex flex-col min-w-0 p-6 md:p-10 gap-6" data-purpose="path-finder-interface">
      <div className="border border-[#2b3440] bg-[#0f141b]/95 rounded-xl p-6 md:p-8 shadow-[0_20px_60px_rgba(0,0,0,0.35)]">
        <h2 className="font-headline font-extrabold text-2xl text-[#eef3f8] tracking-tight mb-2">Network Path Analyzer</h2>
        <p className="text-[#9aa6b4] text-sm font-body mb-6">Find the shortest recruiter-intro chain and surface high-value bridge nodes.</p>

        <div className="flex flex-col md:flex-row gap-4 items-end max-w-4xl">
          <div className="flex-1 w-full space-y-1">
            <label className="font-label text-[10px] text-[#7d8793] uppercase tracking-[0.2em] block">Recruiter LinkedIn</label>
            <input 
              type="text" placeholder="https://www.linkedin.com/in/jane-doe" 
              value={recruiterUrl} onChange={e => setRecruiterUrl(e.target.value)} onKeyDown={handleKey} disabled={isLoading}
              className="w-full bg-[#0a0f15] border border-[#2b3440] px-4 py-3 text-[#edf2f7] font-label focus:outline-none focus:border-[#9db3ca] transition-colors rounded-lg"
            />
          </div>
          <div className="flex-1 w-full space-y-1">
            <label className="font-label text-[10px] text-[#7d8793] uppercase tracking-[0.2em] block">Your LinkedIn ID</label>
            <input 
              type="text" placeholder="https://www.linkedin.com/in/your-linkedin-id" 
              value={yourLinkedInId} onChange={e => setYourLinkedInId(e.target.value)} onKeyDown={handleKey} disabled={isLoading}
              className="w-full bg-[#0a0f15] border border-[#2b3440] px-4 py-3 text-[#edf2f7] font-label focus:outline-none focus:border-[#9db3ca] transition-colors rounded-lg"
            />
          </div>
          <button 
            onClick={() => void submit()} disabled={isLoading}
            className="btn-shine bg-[linear-gradient(120deg,#c9d5e1,#90a5bc)] text-[#0b1118] px-8 py-3 border border-[#b9c8d8] rounded-lg font-label font-bold uppercase tracking-widest text-sm hover:brightness-105 transition-all disabled:opacity-50 shrink-0"
          >
            {isLoading ? 'Scanning...' : 'Find Path'}
          </button>
        </div>
        {error && <p className="text-sm font-label text-red-500 mt-3">{String(error)}</p>}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 border border-[#2b3440] bg-[#0f141b]/95 rounded-xl p-4 md:p-6 overflow-hidden shadow-[0_16px_40px_rgba(0,0,0,0.32)]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-headline text-[#e6edf5] text-lg tracking-tight">Node Bridge Visual</h3>
            <span className={`font-label text-[10px] uppercase tracking-[0.2em] ${isLoading ? 'text-[#aabed2]' : result ? 'text-[#d4dde7]' : 'text-[#7f8a97]'}`}>
              {isLoading ? 'Analyzing' : result ? 'Path Detected' : 'Awaiting Input'}
            </span>
          </div>
          <img
            src="/nodevisual.png"
            alt="Source node to bridge node to destination node"
            className="w-full rounded-lg border border-[#2b3440] object-cover bg-black"
          />

          <div className="mt-4 flex items-center gap-2 text-[#7f8a97] text-xs">
            <span className={`w-2 h-2 rounded-full ${isLoading ? 'bg-[#b8c6d5] animate-pulse' : result ? 'bg-[#d8e2ec]' : 'bg-[#5f6873]'}`} />
            {isLoading ? 'Computing shortest intro chain...' : result ? `Best path found in ${result.query_time_ms.toFixed(0)} ms` : 'Run a scan to compute shortest path and bridge nodes.'}
          </div>
        </div>

        <div className="border border-[#2b3440] bg-[#0f141b]/95 rounded-xl p-6 shadow-[0_16px_40px_rgba(0,0,0,0.32)]">
          <h3 className="font-headline text-[#e6edf5] text-lg tracking-tight mb-5">Path Snapshot</h3>
          {!result && !isLoading && (
            <div className="flex flex-col items-center justify-center opacity-60 min-h-[220px]">
              <Network className="w-14 h-14 text-[#9eb2c7] mb-3" />
              <p className="font-label text-xs text-[#7d8793] uppercase tracking-widest text-center">No path yet</p>
            </div>
          )}
          {isLoading && (
            <div className="space-y-3 min-h-[220px]">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="h-10 rounded-md border border-[#2b3440] bg-[#111923] animate-pulse" />
              ))}
            </div>
          )}
          {result && (
            <div className="space-y-3 max-h-[280px] overflow-y-auto pr-1">
              {result.path.map((node, i) => (
                <div key={`${node.id}-${i}`} className="border border-[#2b3440] rounded-md p-3 bg-[#0b1118]">
                  <div className="text-[#9db3ca] text-[10px] uppercase tracking-[0.18em] font-label">Step {i + 1}</div>
                  <div className="text-[#eef3f8] text-sm font-semibold truncate" title={node.name}>{node.name}</div>
                  <div className="text-[#7c8794] text-[11px] truncate" title={node.headline}>{node.headline}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="border border-[#2b3440] bg-[#0f141b]/95 rounded-xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xs font-bold font-mono tracking-widest text-[#7d8793] uppercase">Bridge Nodes</h2>
            {result && <span className="text-xs text-[#c7d3df] font-mono">{bridges.length} detected</span>}
          </div>

          <div className="space-y-3">
            {!result && <p className="text-xs text-[#647080] font-mono">No active scan.</p>}
            {bridges.map((node) => (
              <div key={node.id} className="flex items-center justify-between border border-[#27303b] rounded-md p-3 bg-[#0b1118]">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 border border-[#303b48] bg-[#101923] rounded-md flex items-center justify-center">
                    <Network className="w-4 h-4 text-[#b4c4d4]" />
                  </div>
                  <span className="text-xs font-mono tracking-tight text-[#dbe5ee] max-w-[230px] truncate">
                    {node.name.toUpperCase().replace(/\s+/g, '_')}
                  </span>
                </div>
                <span className="text-[10px] font-mono text-[#92a4b8]">L_{Math.abs(hashStr(node.id) % 99).toString().padStart(2, '0')}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="border border-[#2b3440] bg-[#0f141b]/95 rounded-xl p-6">
          <div className="flex justify-between items-center mb-6">
             <h2 className="text-xs font-bold font-mono tracking-widest text-[#7d8793] uppercase">Alternative Paths</h2>
             {result && <span className="text-xs text-[#c7d3df] font-mono">{rankedAlternativePaths.length} mapped</span>}
          </div>

          <div className="space-y-3">
            {!result && <p className="text-xs text-[#647080] text-center py-4">No active scan.</p>}

            {result && rankedAlternativePaths.length === 0 && (
              <p className="text-xs text-[#647080] text-center py-4">No alternative path found within max hops.</p>
            )}

            {result && rankedAlternativePaths.map((path, idx) => {
              const hops = Math.max(0, path.length - 1)
              return (
                <article
                  key={idx}
                  className="rounded-xl border border-[#2b3440] bg-[linear-gradient(180deg,#111823,#0d131b)] p-4"
                >
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center justify-center min-w-7 h-7 px-2 rounded-md bg-[#1a2431] text-[#eaf1f8] text-xs font-semibold">
                        #{idx + 1}
                      </span>
                      <div>
                        <p className="text-[11px] text-[#e1e9f2] font-semibold tracking-wide uppercase">
                          {idx === 0 ? 'Best Alternative' : 'Alternative Route'}
                        </p>
                        <p className="text-[10px] text-[#7f8b98]">Route quality ranked by shortest length</p>
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <p className="text-[11px] text-[#d7e2ec] font-semibold">{path.length} nodes</p>
                      <p className="text-[10px] text-[#8e9cad]">{hops} hops</p>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    {path.map((node, nodeIdx) => (
                      <div key={`${node.id}-${nodeIdx}`} className="flex items-center gap-2">
                        <span
                          className="px-2.5 py-1.5 rounded-md border border-[#344150] bg-[#121b26] text-[#dbe6f0] text-[11px]"
                          title={node.name}
                        >
                          {node.name}
                        </span>
                        {nodeIdx < path.length - 1 && (
                          <span className="text-[#708196] text-xs" aria-hidden="true">→</span>
                        )}
                      </div>
                    ))}
                  </div>
                </article>
              )
            })}
          </div>
        </div>
      </div>
    </section>
  )
}
