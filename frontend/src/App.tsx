import { NavLink, Outlet, Routes, Route } from 'react-router-dom'
import { ROUTES } from '@/constants'
import PathFinderPage from '@/pages/PathFinderPage'
import TechStackPage from '@/pages/TechStackPage'

function TopNav() {
  return (
    <nav className="bg-[#000000] border-b border-[#222222] flex justify-between items-center w-full px-6 h-16 fixed top-0 z-50">
      <div className="flex items-center gap-8 h-full">
        <span className="text-xl font-bold text-white flex items-center after:content-['.'] after:text-[#A855F7] after:ml-0.5 font-headline tracking-tight">
          RecruitGraph
        </span>
        <div className="hidden md:flex gap-6 h-full items-end" role="tablist">
          <NavLink
            to={ROUTES.PATH_FINDER}
            className={({ isActive }) =>
              `headline-md font-headline tracking-tight pb-4 transition-colors duration-200 ${
                isActive ? 'text-white border-b-2 border-[#A855F7]' : 'text-[#666666] hover:text-white border-b-2 border-transparent'
              }`
            }
          >
            Network Path Finder
          </NavLink>
          <NavLink
            to={ROUTES.TECH_STACK}
            className={({ isActive }) =>
              `headline-md font-headline tracking-tight pb-4 transition-colors duration-200 ${
                isActive ? 'text-white border-b-2 border-[#A855F7]' : 'text-[#666666] hover:text-white border-b-2 border-transparent'
              }`
            }
          >
            Tech Stack Analyzer
          </NavLink>
        </div>
      </div>
      <div className="flex items-center gap-4 text-[#A855F7]">
        <span className="material-symbols-outlined cursor-pointer hover:opacity-80 transition-opacity">terminal</span>
        <span className="material-symbols-outlined cursor-pointer hover:opacity-80 transition-opacity">settings</span>
        <span className="material-symbols-outlined cursor-pointer hover:opacity-80 transition-opacity">account_circle</span>
      </div>
    </nav>
  )
}

function SideNav() {
  return (
    <aside className="bg-[#0e0e0e] border-r border-[#222222] flex flex-col h-screen fixed left-0 top-16 w-64 hidden md:flex z-40">
      <div className="p-4 mb-4">
        <div className="text-[#666666] font-label uppercase tracking-widest text-[10px]">Version Control</div>
        <div className="text-[#CFC2D6] font-label text-xs mt-1">v2.0.4-SYS</div>
      </div>
      <div className="flex-1">
        <div className="px-2 space-y-1">
          <a className="flex items-center gap-3 px-4 py-3 bg-[#1f1f1f] text-[#A855F7] border-l-2 border-[#A855F7] transition-all duration-150 ease-out font-label uppercase tracking-widest text-xs" href="#">
            <span className="material-symbols-outlined text-sm">grid_view</span> Dashboard
          </a>
          <a className="flex items-center gap-3 px-4 py-3 text-[#666666] hover:bg-[#131313] hover:text-white transition-all duration-150 ease-out font-label uppercase tracking-widest text-xs cursor-default" href="#">
            <span className="material-symbols-outlined text-sm">groups</span> Talent Pool
          </a>
          <a className="flex items-center gap-3 px-4 py-3 text-[#666666] hover:bg-[#131313] hover:text-white transition-all duration-150 ease-out font-label uppercase tracking-widest text-xs cursor-default" href="#">
            <span className="material-symbols-outlined text-sm">account_tree</span> Pipeline
          </a>
          <a className="flex items-center gap-3 px-4 py-3 text-[#666666] hover:bg-[#131313] hover:text-white transition-all duration-150 ease-out font-label uppercase tracking-widest text-xs cursor-default" href="#">
            <span className="material-symbols-outlined text-sm">analytics</span> Reports
          </a>
        </div>
      </div>
      <div className="p-4 border-t border-[#222222] space-y-2 mb-16">
        <a className="flex items-center gap-3 text-[#666666] hover:text-white font-label uppercase tracking-widest text-xs cursor-default" href="#">
          <span className="material-symbols-outlined text-sm">description</span> Documentation
        </a>
        <a className="flex items-center gap-3 text-[#666666] hover:text-white font-label uppercase tracking-widest text-xs cursor-default" href="#">
          <span className="material-symbols-outlined text-sm">help</span> Support
        </a>
      </div>
    </aside>
  )
}

function Layout() {
  return (
    <div className="bg-[#000000] min-h-screen font-body flex">
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
