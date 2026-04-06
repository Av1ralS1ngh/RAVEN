import SkillQuiz from '@/components/dashboard/SkillQuiz'
import TopSkills from '@/components/dashboard/TopSkills'
import { Sparkles, Compass, Globe } from 'lucide-react'

export default function WhatToChoosePage() {
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
          <SkillQuiz />
        </div>
        
        <div className="space-y-6">
          <div className="flex items-center gap-2 mb-4 text-[#9db3ca]">
            <span className="p-1 rounded-md border border-[#2b3440] bg-[#0d1117] icon-sheen-shell"><Compass className="w-5 h-5 icon-silver" /></span>
            <h3 className="text-sm font-label uppercase tracking-widest">Trending Skill Clusters</h3>
          </div>
          <TopSkills />
        </div>
      </div>

      <footer className="mt-10 pt-10 border-t border-[#2b3440]/50">
        <p className="text-[#5f6b7a] text-xs font-mono uppercase tracking-[0.2em] text-center">
          Holistic Growth Engine &bull; System v3.1.0 &bull; Multi-disciplinary Mode
        </p>
      </footer>
    </section>
  )
}
