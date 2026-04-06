import { TrendingUp, Sparkles, Brain, Database, Layers, MessageSquare, Compass, ShieldAlert } from 'lucide-react'

const TOP_SKILLS = [
  {
    category: 'Technical Systems',
    items: [
      {
        title: 'AI Agents & LLMs',
        desc: 'Automating tasks with LangChain and OpenAI.',
        tag: 'Trending',
        icon: <Sparkles className="w-5 h-5 text-purple-400" />
      },
      {
        title: 'TigerGraph Analytics',
        desc: 'Connecting data points for deep graph insights.',
        tag: 'Deep Tech',
        icon: <Database className="w-5 h-5 text-green-400" />
      }
    ]
  },
  {
    category: 'High-Value Human Skills',
    items: [
      {
        title: 'Strategic Storytelling',
        desc: 'Communicating complex tech ideas to stakeholders.',
        tag: 'Multiplier',
        icon: <MessageSquare className="w-5 h-5 text-orange-400" />
      },
      {
        title: 'Agile Product Leadership',
        desc: 'Leading cross-functional teams with empathy.',
        tag: 'Leadership',
        icon: <Compass className="w-5 h-5 text-teal-400" />
      }
    ]
  }
]

export default function TopSkills() {
  return (
    <div className="space-y-10">
      {TOP_SKILLS.map((section, idx) => (
        <div key={idx} className="space-y-6">
          <div className="flex items-center gap-2 mb-4 border-b border-[#2b3440] pb-2">
            {idx === 0 ? <TrendingUp className="w-4 h-4 text-[#9db3ca]" /> : <ShieldAlert className="w-4 h-4 text-orange-400" />}
            <h3 className="text-sm font-label font-bold text-[#eef3f8] uppercase tracking-widest">{section.category}</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {section.items.map((skill, i) => (
              <div 
                key={i} 
                className="group p-6 bg-[#0f141b]/95 border border-[#2b3440] rounded-xl hover:border-[#9db3ca] hover:shadow-[0_10px_40px_rgba(0,0,0,0.3)] transition-all cursor-default"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="p-2 bg-[#0a0f15] rounded-lg border border-[#2b3440] group-hover:border-[#9db3ca] transition-colors">
                    {skill.icon}
                  </div>
                  <span className="text-[10px] font-label text-[#9db3ca] bg-[#1a2431] px-2 py-1 rounded-full uppercase tracking-widest">{skill.tag}</span>
                </div>
                <h4 className="text-lg font-headline font-semibold text-[#eef3f8] mb-2">{skill.title}</h4>
                <p className="text-[#9aa6b4] text-xs font-body leading-relaxed">{skill.desc}</p>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
