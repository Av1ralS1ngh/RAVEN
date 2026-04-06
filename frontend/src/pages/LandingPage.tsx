import { useEffect, useRef } from 'react'
import { ROUTES } from '@/constants'
import { Rocket, Globe } from 'lucide-react'

// Note: Vanta requires Three.js to be in the window or explicitly passed
declare global {
  interface Window {
    VANTA: any
    THREE: any
  }
}

interface LandingPageProps {
  onLaunch: () => void
  isLaunching: boolean
}

export default function LandingPage({ onLaunch, isLaunching }: LandingPageProps) {
  const vantaRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let vantaEffect: any = null
    const scriptThree = document.createElement('script')
    scriptThree.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js'
    scriptThree.async = true
    
    const scriptVanta = document.createElement('script')
    scriptVanta.src = 'https://cdn.jsdelivr.net/npm/vanta@latest/dist/vanta.net.min.js'
    scriptVanta.async = true

    scriptThree.onload = () => {
      document.body.appendChild(scriptVanta)
    }

    scriptVanta.onload = () => {
      if (window.VANTA && vantaRef.current) {
        vantaEffect = window.VANTA.NET({
          el: vantaRef.current,
          mouseControls: true,
          touchControls: true,
          gyroControls: false,
          minHeight: 200.00,
          minWidth: 200.00,
          scale: 1.00,
          scaleMobile: 1.00,
          color: 0x3f5efb,
          backgroundColor: 0x0a0c11,
          points: 10.00,
          maxDistance: 20.00,
          spacing: 15.00
        })
      }
    }

    document.body.appendChild(scriptThree)

    return () => {
      if (vantaEffect) vantaEffect.destroy()
    }
  }, [])

  return (
    <div 
      ref={vantaRef} 
      className={`fixed inset-0 flex items-center justify-center overflow-hidden transition-all duration-700 ${isLaunching ? 'animate-slide-out-up' : ''}`}
    >
      {/* Overlay for better readability */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px]" />
      
      <div className={`relative z-10 text-center px-4 max-w-4xl ${isLaunching ? 'opacity-0' : 'animate-in fade-in zoom-in duration-1000'}`}>
        <div className="flex justify-center mb-8">
            <img 
              src="/raven.png" 
              alt="RAVEN" 
              className={`w-24 h-24 rounded-2xl shadow-[0_0_50px_rgba(255,255,255,0.1)] border border-white/10 ${isLaunching ? 'invisible' : ''}`} 
            />
        </div>
        
        <h1 className="text-6xl md:text-8xl font-headline font-extrabold text-white tracking-tighter mb-4 drop-shadow-2xl">
          RAVEN
        </h1>
        
        <p className="text-lg md:text-2xl font-label text-[#9db3ca] uppercase tracking-[0.4em] mb-12 opacity-80">
          Recruiter Analysis Via Entity Nodes
        </p>

        <div className="flex justify-center">
          <button 
            onClick={onLaunch}
            className="group relative flex items-center gap-4 px-12 py-5 bg-white text-black font-headline font-bold uppercase tracking-widest text-lg rounded-full hover:bg-[#eef3f8] transition-all transform hover:scale-105 active:scale-95 shadow-[0_20px_50px_rgba(255,255,255,0.15)]"
          >
            <Rocket className="w-6 h-6 group-hover:animate-bounce" />
            LET'S STARTED
            <div className="absolute -inset-0.5 bg-gradient-to-r from-[#9db3ca] to-white rounded-full blur opacity-30 group-hover:opacity-50 transition duration-1000 group-hover:duration-200" />
          </button>
        </div>

        <div className="mt-20 flex gap-12 justify-center opacity-40">
           <div className="text-center">
             <div className="text-sm font-mono text-white mb-1 uppercase tracking-widest">Entities</div>
             <div className="text-2xl font-headline text-[#9db3ca]">14.2K+</div>
           </div>
           <div className="text-center">
             <div className="text-sm font-mono text-white mb-1 uppercase tracking-widest">Paths</div>
             <div className="text-2xl font-headline text-[#9db3ca]">8.6M+</div>
           </div>
           <div className="text-center">
             <div className="text-sm font-mono text-white mb-1 uppercase tracking-widest">Latency</div>
             <div className="text-2xl font-headline text-[#9db3ca]">12ms</div>
           </div>
        </div>
      </div>
      
      <footer className="absolute bottom-8 left-0 right-0 text-center z-10 opacity-30">
        <p className="text-[10px] font-mono text-white uppercase tracking-[0.5em]">
          Classified Intelligence Protocol &bull; System Active
        </p>
      </footer>
    </div>
  )
}
