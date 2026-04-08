import { TrendingUp, Sparkles, Database, MessageSquare, Compass, ShieldAlert } from 'lucide-react'
import type { TrendingSkillItem } from '@/types/discovery.types'

const TOP_SKILLS = [
  {
    category: 'Technical Systems',
    items: [
      {
        title: 'AI Agents & LLMs',
        desc: 'Automating tasks with LangChain and OpenAI.',
        tag: 'Trending',
        icon: <Sparkles className="w-5 h-5 icon-silver" />
      },
      {
        title: 'TigerGraph Analytics',
        desc: 'Connecting data points for deep graph insights.',
        tag: 'Deep Tech',
        icon: <Database className="w-5 h-5 icon-silver" />
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
        icon: <MessageSquare className="w-5 h-5 icon-silver" />
      },
      {
        title: 'Agile Product Leadership',
        desc: 'Leading cross-functional teams with empathy.',
        tag: 'Leadership',
        icon: <Compass className="w-5 h-5 icon-silver" />
      }
    ]
  }
]

interface TopSkillsProps {
  trending?: TrendingSkillItem[]
  isLoading?: boolean
}

const TECH_CATEGORIES = new Set(['language', 'framework', 'tool', 'platform', 'database'])

function iconForCategory(category: string) {
  if (category === 'database') {
    return <Database className="w-5 h-5 icon-silver" />
  }
  if (category === 'other') {
    return <MessageSquare className="w-5 h-5 icon-silver" />
  }
  if (category === 'platform') {
    return <Compass className="w-5 h-5 icon-silver" />
  }
  return <Sparkles className="w-5 h-5 icon-silver" />
}

function formatTag(skill: TrendingSkillItem): string {
  if (skill.connected_roles.length >= 3) {
    return 'Cross-Role'
  }
  if (skill.score >= 3) {
    return 'Momentum'
  }
  return 'Emerging'
}

export default function TopSkills({ trending = [], isLoading = false }: TopSkillsProps) {
  const hasTrending = trending.length > 0
  const dynamicSections = [
    {
      category: 'Technical Systems',
      items: trending
        .filter(skill => TECH_CATEGORIES.has(skill.category))
        .slice(0, 4)
        .map(skill => ({
          title: skill.name,
          desc: `${skill.connected_roles.length} aligned role${skill.connected_roles.length === 1 ? '' : 's'} in discovery graph.`,
          tag: formatTag(skill),
          icon: iconForCategory(skill.category),
        })),
    },
    {
      category: 'High-Value Human Skills',
      items: trending
        .filter(skill => !TECH_CATEGORIES.has(skill.category))
        .slice(0, 4)
        .map(skill => ({
          title: skill.name,
          desc: `Influences ${skill.connected_roles.length} discovery pathways.`,
          tag: formatTag(skill),
          icon: iconForCategory(skill.category),
        })),
    },
  ].map(section => ({
    ...section,
    items: section.items.length > 0 ? section.items : [],
  }))

  const sections = hasTrending && dynamicSections.some(section => section.items.length > 0)
    ? dynamicSections
    : TOP_SKILLS

  return (
    <div className="space-y-10">
      {isLoading && (
        <div className="rounded-lg border border-[#2b3440] bg-[#0f141b]/95 p-4 text-xs text-[#9aa6b4] uppercase tracking-[0.16em] animate-pulse">
          Synchronizing trending skills...
        </div>
      )}

      {sections.map((section, idx) => (
        <div key={idx} className="space-y-6">
          <div className="flex items-center gap-2 mb-4 border-b border-[#2b3440] pb-2">
            {idx === 0 ? <TrendingUp className="w-4 h-4 icon-silver" /> : <ShieldAlert className="w-4 h-4 icon-silver" />}
            <h3 className="text-sm font-label font-bold text-[#eef3f8] uppercase tracking-widest">{section.category}</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {section.items.map((skill, i) => (
              <div
                key={i}
                className="group p-6 bg-[#0f141b]/95 border border-[#2b3440] rounded-xl hover:border-[#9db3ca] hover:shadow-[0_10px_40px_rgba(0,0,0,0.3)] transition-all cursor-default"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="p-2 bg-[#0a0f15] rounded-lg border border-[#2b3440] group-hover:border-[#9db3ca] transition-colors icon-sheen-shell">
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
