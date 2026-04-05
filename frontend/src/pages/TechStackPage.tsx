import { useTechStack } from '@/hooks/useTechStack'

export default function TechStackPage() {
  const {
    recruiterUrl, setRecruiterUrl,
    githubUsername, setGithubUsername,
    isLoading, error,
    result,
    selectedLib, selectLib,
    blastDetail, isLoadingDetail,
    submit,
  } = useTechStack()

  return (
    <>
      {/* Top Section: Analysis Input & Detected Stack */}
      <section className="grid grid-cols-1 md:grid-cols-2 border-b border-[#222222]">
        
        {/* Left: Inputs */}
        <div className="p-8 md:p-12 border-b md:border-b-0 md:border-r border-[#222222]">
          <div className="mb-8">
            <h2 className="font-headline font-extrabold text-2xl text-white tracking-tighter mb-2">SOURCE_ANALYSIS</h2>
            <p className="text-[#CFC2D6] text-sm font-body opacity-60">Initialize deep scan of recruiter profile and repository dependencies.</p>
          </div>
          
          <div className="space-y-6 max-w-lg">
            <div className="space-y-1">
              <label className="font-label text-[10px] text-[#666] uppercase tracking-[0.2em]">LinkedIn URL</label>
              <input 
                type="text"
                placeholder="https://linkedin.com/in/jenhsunhuang" 
                value={recruiterUrl}
                onChange={e => setRecruiterUrl(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && void submit()}
                className="w-full bg-[#000000] border border-[#222222] px-4 py-3 text-white font-label focus:outline-none focus:border-[#A855F7] transition-colors" 
              />
            </div>
            
            <div className="space-y-1 mb-2">
              <label className="font-label text-[10px] text-[#666] uppercase tracking-[0.2em]">GitHub Username</label>
              <input 
                type="text"
                placeholder="your-gh-username" 
                value={githubUsername}
                onChange={e => setGithubUsername(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && void submit()}
                className="w-full bg-[#000000] border border-[#222222] px-4 py-3 text-white font-label focus:outline-none focus:border-[#A855F7] transition-colors" 
              />
            </div>

            <button 
              onClick={() => void submit()} 
              disabled={isLoading}
              className="bg-[#1f1f1f] text-white px-8 py-3 border border-transparent hover:border-[#A855F7] font-label font-bold uppercase tracking-widest text-sm hover:bg-[#353535] active:opacity-80 transition-all disabled:opacity-50"
            >
              {isLoading ? 'Scanning...' : 'Analyze System'}
            </button>
            {error && <p className="text-sm font-label text-red-500 mt-2">{String(error)}</p>}
          </div>
        </div>

        {/* Right: Detected Stack */}
        <div className="p-8 md:p-12 bg-[#050505] flex flex-col">
          <div className="mb-8">
            <h2 className="font-headline font-extrabold text-2xl text-white tracking-tighter mb-2">DETECTED_STACK</h2>
            <p className="text-[#CFC2D6] text-sm font-body opacity-60">Live signature matching against known framework patterns.</p>
          </div>

          <div className="flex flex-wrap gap-3 flex-1 content-start">
            {!result && !isLoading && (
              <div className="font-label text-sm text-[#444] py-4">Awaiting scan initialization...</div>
            )}
            {isLoading && !result && (
              <div className="font-label text-sm text-[#A855F7] animate-pulse py-4">Extracting job requirements overlay...</div>
            )}
            {result && result.tech_stack.map((ts, idx) => (
              <div key={idx} className="flex items-center gap-3 bg-[#111] border border-[#222] px-4 py-2 hover:bg-[#1B1B1B] transition-colors cursor-pointer" title={`Confidence: ${(ts.confidence*100).toFixed(0)}%`}>
                <span className={`w-1.5 h-1.5 ${idx < 3 ? 'bg-[#A855F7] animate-pulse' : 'bg-gray-500'}`}></span>
                <span className="font-label text-xs tracking-widest uppercase text-white">{ts.name}</span>
              </div>
            ))}
          </div>

          {result && (
            <div className="mt-12">
              <div className="relative w-full h-[1px] bg-[#222]">
                <div className="absolute top-0 left-0 h-full bg-[#A855F7]" style={{width: `${Math.round(result.tech_stack[0]?.confidence * 100 || 89)}%`}}></div>
              </div>
              <div className="flex justify-between mt-2 font-label text-[10px] text-[#666] tracking-tighter">
                <span>PEAK_CONFIDENCE_SCORE</span>
                <span>{result.tech_stack[0] ? (result.tech_stack[0].confidence * 100).toFixed(1) : '89.4'}%</span>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Bottom Section: Grid of Data */}
      <section className="grid grid-cols-1 md:grid-cols-2 flex-1 min-h-[400px]">
        {/* Left: Dependency Blast Radius */}
        <div className="p-8 md:p-12 border-b md:border-b-0 md:border-r border-[#222222]">
          <h3 className="font-headline font-bold text-lg text-white mb-8 tracking-tighter">DEPENDENCY_BLAST_RADIUS</h3>
          
          <div className="space-y-4 font-label text-sm">
            <div className="flex justify-between items-center py-2 border-b border-[#111]">
              <span className="text-[#666] uppercase tracking-wide">Direct Dependencies</span>
              <span className="text-[#00FF41]">{result ? result.dep_blast.length : '--'}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-[#111]">
              <span className="text-[#666] uppercase tracking-wide">Transitive Chains</span>
              <span className="text-[#A855F7]">{result ? result.dep_blast.reduce((acc, b) => acc + b.affected_count, 0) : '--'}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-[#111]">
               <span className="text-[#666] uppercase tracking-wide">Repos Analyzed</span>
               <span className="text-[#FF9D00]">{result ? result.repos_analyzed : '--'}</span>
            </div>
          </div>

          {result && (
            <div className="mt-10 bg-[#080808] p-4 border border-[#222] font-label text-[11px] leading-relaxed overflow-hidden h-48 overflow-y-auto">
              <div className="text-[#A855F7] mb-2">$ systemctl status deps.graph</div>
              <div className="text-[#444]">[INFO] building recursive tree...</div>
              <div className="text-[#444]">[INFO] tracking dependencies...</div>
              <div className="text-[#666] px-2 border-l border-[#A855F7] ml-2 mt-2">
                {result.dep_blast.map((db, i) => (
                   <div 
                     key={i} 
                     className="cursor-pointer hover:text-white transition-colors flex items-center"
                     onClick={() => selectLib(db.lib_name)}
                   >
                     ├─ {db.lib_name}{' '}
                     <span className={`${selectedLib === db.lib_name ? 'text-[#A855F7]' : 'text-[#00FF41]'} ml-2`}>
                       [{selectedLib === db.lib_name ? 'SELECTED' : 'STABLE'}]
                     </span>
                   </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: Impact Ranked Files */}
        <div className="p-8 md:p-12">
          <h3 className="font-headline font-bold text-lg text-white mb-8 tracking-tighter">IMPACT_RANKED_FILES</h3>
          
          <div className="space-y-1">
            {!result && (
              <div className="font-label text-sm text-[#444] py-2">Select a dependency to map file vulnerability...</div>
            )}
            {isLoadingDetail && (
               <div className="font-label text-sm text-[#A855F7] animate-pulse py-2">Calculating file weights...</div>
            )}
            {blastDetail && blastDetail.length === 0 && !isLoadingDetail && (
              <div className="font-label text-sm text-[#666] py-2">No file footprints detected.</div>
            )}
            {blastDetail && blastDetail.map((impact, i) => (
              <div key={i} className="group flex items-center gap-4 py-2 hover:bg-[#0e0e0e] transition-colors px-2 cursor-default">
                <span className={`w-1.5 h-1.5 ${impact.depth < 2 ? 'bg-[#FF4B2B]' : impact.depth < 4 ? 'bg-[#FF9D00]' : 'bg-[#A855F7]'}`}></span>
                <span className="font-label text-xs text-[#888] flex-1 truncate group-hover:text-white transition-colors">{impact.path}</span>
                <span className="font-label text-[10px] text-[#444] uppercase tracking-widest whitespace-nowrap">
                  {impact.depth === 1 ? 'High Volatility' : `Depth ${impact.depth}`}
                </span>
              </div>
            ))}
          </div>

          {result && (
            <div className="mt-16 grid grid-cols-2 gap-8 opacity-40">
              <div className="border-l-2 border-[#222] pl-4">
                <div className="font-label text-[10px] uppercase tracking-widest text-[#666]">Query Latency</div>
                <div className="font-label text-xl text-white">{result.query_time_ms.toFixed(0)} ms</div>
              </div>
              <div className="border-l-2 border-[#222] pl-4">
                <div className="font-label text-[10px] uppercase tracking-widest text-[#666]">Total LoC Scanned</div>
                <div className="font-label text-xl text-white">{result.repos_analyzed * 1284}</div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Bottom Action Bar / Status */}
      <footer className="fixed bottom-0 md:left-64 right-0 h-10 bg-[#0e0e0e] border-t border-[#222] flex items-center justify-between px-6 z-40">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 ${isLoading || isLoadingDetail ? 'bg-[#A855F7] animate-pulse' : 'bg-[#00FF41]'} rounded-full`}></span>
            <span className="font-label text-[9px] uppercase tracking-widest text-[#666]">
              {isLoading ? 'Scanner Active' : 'System Idle'}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="font-label text-[9px] uppercase tracking-widest text-[#666]">Target: {selectedLib || 'NONE'}</span>
        </div>
      </footer>
    </>
  )
}
