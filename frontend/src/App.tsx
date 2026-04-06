import { NavLink, Outlet, Routes, Route } from 'react-router-dom'
import { ROUTES } from '@/constants'
import PathFinderPage from '@/pages/PathFinderPage'
import TechStackPage from '@/pages/TechStackPage'

function TopNav() {
  return (
    <nav className="bg-[#0a0d11]/95 backdrop-blur border-b border-[#2b3440] flex justify-between items-center w-full px-6 h-16 fixed top-0 z-50">
      <div className="flex items-center gap-8 h-full">
        <span className="text-xl font-bold text-[#edf2f7] flex items-center after:content-['.'] after:text-[#8ea6bf] after:ml-0.5 font-headline tracking-tight">
          RecruitGraph
        </span>
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
      <div className="flex-1">
        <div className="px-2 space-y-1">
          <a className="flex items-center gap-3 px-4 py-3 bg-[#141a22] text-[#d8e2ec] border-l-2 border-[#9db3ca] transition-all duration-150 ease-out font-label uppercase tracking-widest text-xs" href="#">
            <span className="material-symbols-outlined text-sm">grid_view</span> Dashboard
          </a>
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
  return (
    <div className="min-h-screen font-body flex bg-[radial-gradient(circle_at_16%_0%,#1d2631_0%,#0b0e13_36%,#090b0f_100%)]">
      <div className="pointer-events-none fixed inset-0 opacity-60 bg-[radial-gradient(circle_at_82%_22%,rgba(179,199,220,0.16),transparent_34%),radial-gradient(circle_at_35%_82%,rgba(152,168,184,0.08),transparent_42%)]" />
      <TopNav />
      <SideNav />
      {/* Main Canvas */}
      <main className="pl-0 md:pl-64 pt-16 min-h-screen w-full flex flex-col relative overflow-x-hidden">
        <Outlet />
      </main>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path={ROUTES.PATH_FINDER} element={<PathFinderPage />} />
        <Route path={ROUTES.TECH_STACK} element={<TechStackPage />} />
      </Route>
    </Routes>
  )
}
