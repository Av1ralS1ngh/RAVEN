import { NavLink, Outlet, Routes, Route, Link, useNavigate, useLocation } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import { ROUTES } from '@/constants'
import LandingPage from '@/pages/LandingPage'
import PathFinderPage from '@/pages/PathFinderPage'
import TechStackPage from '@/pages/TechStackPage'
import WhatToChoosePage from '@/pages/WhatToChoosePage'

function TopNav() {
  return (
    <nav className="bg-[#0a0d11]/95 backdrop-blur border-b border-[#2b3440] flex justify-between items-center w-full px-6 h-16 fixed top-0 z-50">
      <div className="flex items-center gap-8 h-full">
        <Link 
          to={ROUTES.LANDING}
          className="flex items-center gap-2.5 text-xl font-bold text-[#edf2f7] font-headline tracking-tight hover:opacity-80 transition-opacity"
        >
          <img src="/raven.png" alt="RAVEN logo" className="w-8 h-8 rounded-sm object-cover" />
          <span>RAVEN</span>
        </Link>
        <div className="hidden md:flex gap-6 h-full items-end" role="tablist">
          <NavLink
            to={ROUTES.PATH_FINDER}
            className={({ isActive }) =>
              `headline-md font-headline tracking-tight pb-4 transition-colors duration-200 ${
                isActive ? 'text-[#eef3f8] border-b-2 border-[#9db3ca]' : 'text-[#7d8793] hover:text-[#e6ebf1] border-b-2 border-transparent'
              }`
            }
          >
            Network Path Finder
          </NavLink>
          <NavLink
            to={ROUTES.TECH_STACK}
            className={({ isActive }) =>
              `headline-md font-headline tracking-tight pb-4 transition-colors duration-200 ${
                isActive ? 'text-[#eef3f8] border-b-2 border-[#9db3ca]' : 'text-[#7d8793] hover:text-[#e6ebf1] border-b-2 border-transparent'
              }`
            }
          >
            Tech Stack Analyzer
          </NavLink>
          <NavLink
            to={ROUTES.WHAT_TO_CHOOSE}
            className={({ isActive }) =>
              `headline-md font-headline tracking-tight pb-4 transition-colors duration-200 ${
                isActive ? 'text-[#eef3f8] border-b-2 border-[#9db3ca]' : 'text-[#7d8793] hover:text-[#e6ebf1] border-b-2 border-transparent'
              }`
            }
          >
            Skill Discovery
          </NavLink>
        </div>
      </div>
      <div className="flex items-center gap-4 text-[#9db3ca]">
        <span className="material-symbols-outlined cursor-pointer hover:opacity-80 transition-opacity">terminal</span>
        <span className="material-symbols-outlined cursor-pointer hover:opacity-80 transition-opacity">settings</span>
        <span className="material-symbols-outlined cursor-pointer hover:opacity-80 transition-opacity">account_circle</span>
      </div>
    </nav>
  )
}

function SideNav() {
  return (
    <aside className="bg-[#0d1116] border-r border-[#2b3440] flex flex-col h-screen fixed left-0 top-16 w-64 hidden md:flex z-40">
      <div className="p-4 mb-4">
        <div className="text-[#768293] font-label uppercase tracking-widest text-[10px]">Version Control</div>
        <div className="text-[#c8d2dd] font-label text-xs mt-1">v2.0.4-SYS</div>
      </div>
      <div className="flex-1 overflow-y-auto">
        <div className="px-2 space-y-1">
          <NavLink
            to={ROUTES.PATH_FINDER}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 transition-all duration-150 ease-out font-label uppercase tracking-widest text-xs border-l-2 ${
                isActive ? 'bg-[#141a22] text-[#d8e2ec] border-[#9db3ca]' : 'text-[#7d8793] hover:text-[#e6ebf1] border-transparent'
              }`
            }
          >
            <span className="material-symbols-outlined text-sm">grid_view</span> Dashboard
          </NavLink>
          <NavLink
            to={ROUTES.WHAT_TO_CHOOSE}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 transition-all duration-150 ease-out font-label uppercase tracking-widest text-xs border-l-2 ${
                isActive ? 'bg-[#141a22] text-[#d8e2ec] border-[#9db3ca]' : 'text-[#7d8793] hover:text-[#e6ebf1] border-transparent'
              }`
            }
          >
            <span className="material-symbols-outlined text-sm">explore</span> Skill Discovery
          </NavLink>
        </div>
      </div>
      <div className="p-4 border-t border-[#2b3440] space-y-2 mb-16">
        <a className="flex items-center gap-3 text-[#7d8793] hover:text-[#e6ebf1] font-label uppercase tracking-widest text-xs cursor-default" href="#">
          <span className="material-symbols-outlined text-sm">description</span> Documentation
        </a>
        <a className="flex items-center gap-3 text-[#7d8793] hover:text-[#e6ebf1] font-label uppercase tracking-widest text-xs cursor-default" href="#">
          <span className="material-symbols-outlined text-sm">help</span> Support
        </a>
      </div>
    </aside>
  )
}

function Layout() {
  const location = useLocation()
  const isLanding = location.pathname === ROUTES.LANDING

  return (
    <div className={`min-h-screen font-body flex bg-[radial-gradient(circle_at_16%_0%,#1d2631_0%,#0b0e13_36%,#090b0f_100%)] ${!isLanding ? 'animate-fade-in-dashboard' : ''}`}>
      {!isLanding && (
        <>
          <div className="pointer-events-none fixed inset-0 opacity-60 bg-[radial-gradient(circle_at_82%_22%,rgba(179,199,220,0.16),transparent_34%),radial-gradient(circle_at_35%_82%,rgba(152,168,184,0.08),transparent_42%)]" />
          <TopNav />
          <SideNav />
        </>
      )}
      {/* Main Canvas */}
      <main className={`${isLanding ? 'pl-0 pt-0' : 'pl-0 md:pl-64 pt-16'} min-h-screen w-full flex flex-col relative overflow-x-hidden`}>
        <Outlet />
      </main>
    </div>
  )
}

export default function App() {
  const [isLaunching, setIsLaunching] = useState(false)
  const navigate = useNavigate()
  const flapAudio = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    flapAudio.current = new Audio('https://assets.mixkit.co/sfx/download/mixkit-large-bird-flapping-wings-2481.wav')
    flapAudio.current.volume = 0.5
  }, [])

  const handleLaunch = () => {
    setIsLaunching(true)
    flapAudio.current?.play().catch(e => console.log("Audio failed:", e))
    
    // Duration of index.css animations (1.2s for lift)
    setTimeout(() => {
      navigate(ROUTES.PATH_FINDER)
      setIsLaunching(false)
    }, 1200)
  }

  return (
    <>
      <Routes>
        <Route element={<Layout />}>
          <Route path={ROUTES.LANDING} element={<LandingPage onLaunch={handleLaunch} isLaunching={isLaunching} />} />
          <Route path={ROUTES.PATH_FINDER} element={<PathFinderPage />} />
          <Route path={ROUTES.WHAT_TO_CHOOSE} element={<WhatToChoosePage />} />
          <Route path={ROUTES.TECH_STACK} element={<TechStackPage />} />
        </Route>
      </Routes>

      {/* Transition Overlay */}
      {isLaunching && (
        <div className="fixed inset-0 z-[100] pointer-events-none">
          <img 
            src="/raven.png" 
            alt="RAVEN" 
            className="fixed w-48 h-48 rounded-2xl animate-raven-lift z-[101]"
          />
          {/* Internal Flap Jitter wrapper */}
          <div className="fixed w-48 h-48 animate-raven-flap" style={{ top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
             {/* This empty div follows the lift parent but adds jitter */}
          </div>
        </div>
      )}
    </>
  )
}
