import { useCallback } from 'react'
import { usePathFinder } from '@/hooks/usePathFinder'
import { Network } from 'lucide-react'

// Simple pseudo-random helper for generating fake latency / chart data based on ID
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

  return (
    <section className="flex-1 flex flex-col min-w-0" data-purpose="path-finder-interface">
      {/* Top Header Row for specific inputs, matching TechStack style */}
      <div className="border-b border-[#222222] p-8">
        <h2 className="font-headline font-extrabold text-2xl text-white tracking-tighter mb-4">NETWORK_PATH_FINDER</h2>
        <div className="flex flex-col md:flex-row gap-4 items-end max-w-3xl">
          <div className="flex-1 w-full space-y-1">
            <label className="font-label text-[10px] text-[#666] uppercase tracking-[0.2em] block">Recruiter LinkedIn</label>
            <input 
              type="text" placeholder="https://www.linkedin.com/in/jane-doe" 
              value={recruiterUrl} onChange={e => setRecruiterUrl(e.target.value)} onKeyDown={handleKey} disabled={isLoading}
              className="w-full bg-[#000000] border border-[#222222] px-4 py-3 text-white font-label focus:outline-none focus:border-[#A855F7] transition-colors" 
            />
          </div>
          <div className="flex-1 w-full space-y-1">
            <label className="font-label text-[10px] text-[#666] uppercase tracking-[0.2em] block">Your ID</label>
            <input 
              type="text" placeholder="john-doe" 
              value={yourLinkedInId} onChange={e => setYourLinkedInId(e.target.value)} onKeyDown={handleKey} disabled={isLoading}
              className="w-full bg-[#000000] border border-[#222222] px-4 py-3 text-white font-label focus:outline-none focus:border-[#A855F7] transition-colors" 
            />
          </div>
          <button 
            onClick={() => void submit()} disabled={isLoading}
            className="bg-[#1f1f1f] text-white px-8 py-3 border border-transparent hover:border-[#A855F7] font-label font-bold uppercase tracking-widest text-sm hover:bg-[#353535] transition-all disabled:opacity-50 shrink-0"
          >
            {isLoading ? 'Scanning...' : 'Find Path'}
          </button>
        </div>
        {error && <p className="text-sm font-label text-red-500 mt-3">{String(error)}</p>}
      </div>

      <div className="flex-1 flex flex-col p-8 bg-[#000]">
        {/* Visualization Centerpiece */}
        <div className="w-full flex flex-col min-h-[400px] mb-8 bg-black border border-[#222222] p-12 relative overflow-hidden group">
          <div className="absolute top-4 left-4 flex gap-2 items-center">
            <span className={`w-2 h-2 ${isLoading ? 'bg-[#A855F7] animate-pulse' : result ? 'bg-green-500' : 'bg-gray-600'} rounded-full`}></span>
            <span className="text-[9px] font-mono text-[#666] uppercase tracking-tighter">
              {isLoading ? 'TRACING_NETWORK_GRAPH' : result ? 'LIVE_DATA_STREAM' : 'SYSTEM_STANDBY'}
            </span>
          </div>

          <div className="flex-1 flex items-center justify-center relative z-10 w-full">
            {!result && !isLoading && (
              <div className="flex flex-col items-center justify-center opacity-40">
                <Network className="w-16 h-16 text-[#A855F7] mb-4" />
                <p className="font-label text-sm text-[#666] uppercase tracking-widest">Input targets to begin topological scan</p>
              </div>
            )}
            {isLoading && !result && (
              <div className="w-full h-full flex items-center justify-center">
                <div className="flex gap-4">
                  {[1, 2, 3, 4, 5].map(i => (
                    <div key={i} className="w-16 h-16 border border-[#A855F7]/30 bg-[#A855F7]/5 animate-pulse" style={{ animationDelay: `${i * 150}ms` }} />
                  ))}
                </div>
              </div>
            )}
            {result && (
              <div className="flex items-center gap-2 overflow-x-auto w-full py-8 custom-scrollbar">
                {result.path.map((node, i) => (
                  <div key={node.id} className="flex items-center gap-2 shrink-0">
                    <div className="border border-[#A855F7] bg-[#111] p-4 flex flex-col min-w-[140px]">
                      <span className="font-label text-xs text-[#A855F7] mb-1">NODE_{i.toString().padStart(2, '0')}</span>
                      <span className="font-bold text-white text-sm truncate max-w-[120px]" title={node.name}>{node.name}</span>
                      <span className="text-[10px] text-[#666] truncate max-w-[120px] font-mono mt-1" title={node.headline}>{node.headline}</span>
                    </div>
                    {i < result.path.length - 1 && (
                      <div className="w-8 h-[1px] bg-[#A855F7] relative">
                         <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-[#A855F7] rounded-full"></div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="absolute bottom-4 right-4 text-[9px] font-mono text-[#666] text-right">
            PROTO: SECURE_V3<br/>
            ENCRYPT: AES_256_GCM
          </div>
          {/* Subtle grid background */}
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none transition-opacity duration-1000 opacity-20 group-hover:opacity-40"></div>
        </div>

        {/* Bottom Data Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 border-t border-l border-[#222222]">
          
          {/* Bridge Nodes Card */}
          <div className="border-b border-r border-[#222222] p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xs font-bold font-mono tracking-widest text-[#666] uppercase">Bridge Nodes</h2>
              {result && <span className="text-xs text-[#A855F7] font-mono">{bridges.length} detected</span>}
            </div>
            
            <div className="space-y-4">
              {!result && <p className="text-xs text-[#444] font-mono">No active scan.</p>}
              {bridges.map((node) => (
                <div key={node.id} className="flex items-center justify-between group cursor-default">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 border border-[#222] bg-[#111] flex items-center justify-center">
                      <Network className="w-4 h-4 text-[#666] group-hover:text-[#A855F7] transition-colors" />
                    </div>
                    <span className="text-xs font-mono tracking-tight group-hover:text-white text-[#888] transition-colors max-w-[200px] truncate">
                      {node.name.toUpperCase().replace(/\s+/g, '_')}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-[#666]">L_{Math.abs(hashStr(node.id) % 99).toString().padStart(2, '0')}</span>
                    <div className="w-1.5 h-1.5 rounded-full bg-[#A855F7]"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Alternative Paths Card */}
          <div className="border-b border-r border-[#222222] p-6">
            <div className="flex justify-between items-center mb-6">
               <h2 className="text-xs font-bold font-mono tracking-widest text-[#666] uppercase">Alternative Paths</h2>
               {result && <span className="text-xs text-[#A855F7] font-mono">{result.alternative_paths.length} mapped</span>}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-[10px]">
                <thead>
                  <tr className="text-[#666] border-b border-[#222222]">
                    <th className="pb-3 font-normal uppercase tracking-tighter">Route_ID</th>
                    <th className="pb-3 font-normal uppercase tracking-tighter text-center">Efficiency_Graph</th>
                    <th className="pb-3 font-normal uppercase tracking-tighter text-right">Latency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#222222]">
                  {!result && (
                    <tr>
                      <td colSpan={3} className="py-4 text-[#444] text-center">No active scan.</td>
                    </tr>
                  )}
                  {result && result.alternative_paths.map((path, idx) => {
                     const fakeRouteId = `RT_${String.fromCharCode(65+idx)}${Math.abs(hashStr(path[1].id)%999)}`
                     const opacity = idx === 0 ? '' : idx % 2 === 0 ? 'opacity-40' : 'opacity-60'
                     return (
                       <tr key={idx} className="hover:bg-[#111] transition-colors">
                         <td className="py-4 text-white">{fakeRouteId}</td>
                         <td className="py-4 min-w-[100px]">
                           <svg className={`w-full h-4 text-[#A855F7] ${opacity}`} viewBox="0 0 100 20" preserveAspectRatio="none">
                             <polyline 
                               fill="none" 
                               points={`0,${15-idx} 10,${12+idx} 20,${18-idx} 40,5 60,15 80,${10+idx} 100,6`} 
                               stroke="currentColor" 
                               strokeWidth="1.5"
                             ></polyline>
                           </svg>
                         </td>
                         <td className="py-4 text-right text-[#666]">0.0{20 + Math.abs(hashStr(fakeRouteId)%80)}ms</td>
                       </tr>
                     )
                  })}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}
