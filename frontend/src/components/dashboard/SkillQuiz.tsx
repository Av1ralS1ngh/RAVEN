import React, { useState } from 'react'
import { CheckCircle2, ChevronRight, ChevronLeft, Target, Lightbulb, Sparkles, Heart, Users, BrainCircuit, Zap, BarChart3, Rocket, Globe } from 'lucide-react'

interface Question {
  id: string
  text: string
  options: { value: string; label: string; icon?: React.ReactNode }[]
}

const QUESTIONS: Question[] = [
  {
    id: 'background',
    text: 'What describes your current background?',
    options: [
      { value: 'creative', label: 'Artistic / Visual Enthusiast', icon: <Sparkles className="w-5 h-5 icon-silver" /> },
      { value: 'logical', label: 'Logical / Analytical Thinker', icon: <Target className="w-5 h-5 icon-silver" /> },
      { value: 'people', label: 'People / Strategy Oriented', icon: <Users className="w-5 h-5 icon-silver" /> }
    ]
  },
  {
    id: 'intensity',
    text: 'What kind of work environment do you thrive in?',
    options: [
      { value: 'startup', label: 'High-speed / Rapid Iteration', icon: <Zap className="w-5 h-5 icon-silver" /> },
      { value: 'corporate', label: 'Stable / Process-driven', icon: <BarChart3 className="w-5 h-5 icon-silver" /> },
      { value: 'research', label: 'Deep / R&D Focused', icon: <Rocket className="w-5 h-5 icon-silver" /> }
    ]
  },
  {
    id: 'solving',
    text: 'How do you prefer solving problems?',
    options: [
      { value: 'code', label: 'Building technical systems', icon: <BrainCircuit className="w-5 h-5 icon-silver" /> },
      { value: 'ux', label: 'Improving user experience', icon: <Heart className="w-5 h-5 icon-silver" /> },
      { value: 'strategy', label: 'Defining product strategy', icon: <Lightbulb className="w-5 h-5 icon-silver" /> }
    ]
  },
  {
    id: 'influence',
    text: 'What gives you the most satisfaction?',
    options: [
      { value: 'impact', label: 'Seeing many people use my work', icon: <Users className="w-5 h-5 icon-silver" /> },
      { value: 'elegance', label: 'Creating clean, complex systems', icon: <Target className="w-5 h-5 icon-silver" /> },
      { value: 'creation', label: 'Bringing new ideas to life', icon: <Sparkles className="w-5 h-5 icon-silver" /> }
    ]
  },
  {
    id: 'breadth',
    text: 'How do you like to learn?',
    options: [
      { value: 'generalist', label: 'A bit of everything (Broad)', icon: <Globe className="w-5 h-5 icon-silver" /> },
      { value: 'specialist', label: 'One thing very deeply (Deep)', icon: <Target className="w-4 h-4 icon-silver" /> }
    ]
  }
]

export default function SkillQuiz() {
  const [currentStep, setCurrentStep] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [showResult, setShowResult] = useState(false)

  const handleOptionSelect = (value: string) => {
    const newAnswers = { ...answers, [QUESTIONS[currentStep].id]: value }
    setAnswers(newAnswers)

    if (currentStep < QUESTIONS.length - 1) {
      setCurrentStep(prev => prev + 1)
    } else {
      setShowResult(true)
    }
  }

  const getRecommendation = () => {
    const { background, solving, intensity, influence, breadth } = answers

    // Logic for AI Product Lead
    if (background === 'people' && solving === 'strategy' && influence === 'impact') {
      return {
        title: 'AI Product Lead',
        desc: 'You excel at bridging human needs with high-intensity tech. Master Product Strategy, LLM-Ops, and Agile Leadership to drive global-scale products.'
      }
    }

    // Logic for Creative Developer
    if (background === 'creative' || solving === 'ux') {
      if (breadth === 'specialist') {
        return {
          title: 'Design Systems Architect',
          desc: 'You have a deep eye for precision. Specialize in CSS Architecture, Framer Motion, and design tool integrations like Figma APIs.'
        }
      }
      return {
        title: 'Creative Frontend Engineer',
        desc: 'Combine art with code. Master React, Three.js, and modern UX principles to build stunning interactive experiences.'
      }
    }

    // Logic for System Engineer / R&D
    if (background === 'logical' && solving === 'code') {
      if (intensity === 'research' || breadth === 'specialist') {
        return {
          title: 'Graph Database & Backend Researcher',
          desc: 'You think deep. Specialize in TigerGraph, Distributed Systems, and Performance Optimization at the core level.'
        }
      }
      return {
        title: 'Full-Stack Solutions Architect',
        desc: 'You like building end-to-end. Master the complete stack from database schemas to high-performance APIs and scalable frontends.'
      }
    }

    // Default Fallback
    return {
      title: 'Technical Generalist / PM',
      desc: 'Your versatile skills make you a high-value team bridge. Focus on broad tech literacy while sharpening your strategic decision-making.'
    }
  }

  if (showResult) {
    const recommendation = getRecommendation()
    return (
      <div className="bg-[#0f141b]/95 border border-[#2b3440] rounded-xl p-8 shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-500 min-h-[400px] flex flex-col justify-center">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg border border-[#2b3440] bg-[#0d1117] icon-sheen-shell">
            <CheckCircle2 className="w-8 h-8 icon-silver" />
          </div>
          <h3 className="text-2xl font-headline font-bold text-[#eef3f8]">{recommendation.title}</h3>
        </div>
        <p className="text-[#9aa6b4] mb-8 leading-relaxed text-lg">{recommendation.desc}</p>
        <div className="mt-auto pt-6 border-t border-[#2b3440]/50">
          <button
            onClick={() => { setCurrentStep(0); setShowResult(false); setAnswers({}); }}
            className="px-6 py-2 bg-[#1a2431] border border-[#2b3440] text-[#d8e2ec] rounded-lg hover:bg-[#232d3a] transition-all text-sm font-label uppercase tracking-widest"
          >
            Retake Discovery
          </button>
        </div>
      </div>
    )
  }

  const q = QUESTIONS[currentStep]

  return (
    <div className="bg-[#0f141b]/95 border border-[#2b3440] rounded-xl p-8 shadow-2xl min-h-[500px] flex flex-col">
      <div className="mb-10">
        <div className="flex justify-between items-center mb-4">
          <span className="text-[10px] font-label text-[#7d8793] uppercase tracking-widest">Protocol Step {currentStep + 1} of {QUESTIONS.length}</span>
          <div className="flex gap-1.5">
            {QUESTIONS.map((_, i) => (
              <div key={i} className={`h-1 w-6 rounded-full transition-all ${i <= currentStep ? 'bg-[#9db3ca]' : 'bg-[#2b3440]/60'}`} />
            ))}
          </div>
        </div>
        <h3 className="text-2xl font-headline font-bold text-[#eef3f8] tracking-tight">{q.text}</h3>
      </div>

      <div className="grid grid-cols-1 gap-4 flex-1">
        {q.options.map((opt) => (
          <button
            key={opt.value}
            onClick={() => handleOptionSelect(opt.value)}
            className="group flex items-center justify-between p-5 bg-[#0a0f15] border border-[#2b3440] rounded-xl hover:border-[#9db3ca] hover:bg-[#111822] hover:shadow-[0_4px_20px_rgba(0,0,0,0.2)] transition-all text-left"
          >
            <div className="flex items-center gap-4">
              <div className="p-2.5 bg-[#0d1117] rounded-lg border border-[#2b3440] group-hover:border-[#9db3ca] group-hover:scale-105 transition-all icon-sheen-shell">
                {opt.icon}
              </div>
              <span className="text-[#edf2f7] font-medium leading-tight">{opt.label}</span>
            </div>
            <ChevronRight className="w-4 h-4 text-[#7d8793] group-hover:translate-x-1 transition-transform" />
          </button>
        ))}
      </div>

      <footer className="mt-8 flex items-center justify-between pt-6 border-t border-[#2b3440]/50">
        {currentStep > 0 ? (
          <button
            onClick={() => setCurrentStep(prev => prev - 1)}
            className="flex items-center gap-2 text-[#7d8793] hover:text-[#edf2f7] transition-colors text-xs font-label uppercase tracking-widest"
          >
            <ChevronLeft className="w-4 h-4" /> Back
          </button>
        ) : <div />}
        <span className="text-[10px] font-mono text-[#4a5568] uppercase tracking-[0.2em] animate-pulse">Analyzing...</span>
      </footer>
    </div>
  )
}
