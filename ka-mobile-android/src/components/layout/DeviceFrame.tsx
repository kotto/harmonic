import { useState, useEffect, ReactNode } from 'react'

interface DeviceFrameProps {
  children: ReactNode
}

export default function DeviceFrame({ children }: DeviceFrameProps) {
  const [time, setTime] = useState('')

  useEffect(() => {
    function tick() {
      const n = new Date()
      setTime(
        String(n.getHours()).padStart(2, '0') +
        ':' +
        String(n.getMinutes()).padStart(2, '0'),
      )
    }
    tick()
    const iv = setInterval(tick, 10000)
    return () => clearInterval(iv)
  }, [])

  return (
    <div className="dv relative flex flex-col overflow-hidden"
      style={{
        width: '375px',
        height: '812px',
        borderRadius: 'var(--r-frame, 48px)',
        border: 'var(--bw, 1px) solid rgba(45,212,191,0.10)',
        background: 'radial-gradient(ellipse at 48% 16%, #002435 0%, #001520 42%, #000508 100%)',
        boxShadow: '0 56px 108px rgba(0,0,0,0.95), 0 0 0 0.5px rgba(45,212,191,0.12) inset',
      }}
    >
      {/* Orbs */}
      <div className="orb o1" />
      <div className="orb o2" />
      <div className="orb o3" />

      {/* Status Bar */}
      <div className="flex shrink-0 items-center justify-between px-7 pb-[10px] pt-4 relative z-10">
        <div className="text-[15.5px] font-medium tracking-[-.015em] tabular-nums text-[rgba(230,255,250,0.97)]">
          {time}
        </div>
        <div className="flex items-center gap-[5px]">
          {/* Signal bars */}
          <svg width="17" height="12" viewBox="0 0 17 12" fill="none" aria-hidden="true">
            <rect x="0" y="8" width="3" height="4" rx="1" fill="rgba(230,255,250,0.38)"/>
            <rect x="4.8" y="5.5" width="3" height="6.5" rx="1" fill="rgba(230,255,250,0.52)"/>
            <rect x="9.6" y="3" width="3" height="9" rx="1" fill="rgba(230,255,250,0.66)"/>
            <rect x="14.4" y=".5" width="2.6" height="11.5" rx="1" fill="rgba(230,255,250,0.85)"/>
          </svg>
          {/* WiFi */}
          <svg width="16" height="12" viewBox="0 0 16 12" fill="none" aria-hidden="true">
            <path d="M8 10a1.2 1.2 0 100 2.4A1.2 1.2 0 008 10z" fill="rgba(230,255,250,0.85)"/>
            <path d="M4 7.4a5.6 5.6 0 018 0" stroke="rgba(230,255,250,0.58)" strokeWidth="1.2" strokeLinecap="round" fill="none"/>
            <path d="M.8 4.2a10 10 0 0114.4 0" stroke="rgba(230,255,250,0.34)" strokeWidth="1.2" strokeLinecap="round" fill="none"/>
          </svg>
          {/* Battery */}
          <svg width="27" height="13" viewBox="0 0 27 13" fill="none" aria-hidden="true">
            <rect x=".5" y=".5" width="23" height="12" rx="2.5" stroke="rgba(230,255,250,0.4)" strokeWidth="1"/>
            <rect x="2" y="2" width="17" height="9" rx="1.5" fill="rgba(77,232,174,0.88)"/>
            <path d="M24.5 4.5v4a2 2 0 000-4z" fill="rgba(230,255,250,0.42)"/>
          </svg>
        </div>
      </div>

      {/* Screen content */}
      <div className="flex-1 flex flex-col overflow-hidden min-h-0 relative">
        {children}
      </div>

      <style>{`
        @media (max-width: 420px) {
          .dv {
            width: 100vw !important;
            height: 100dvh !important;
            border-radius: 0 !important;
            border: none !important;
            box-shadow: none !important;
          }
        }
        .orb {
          position: absolute;
          border-radius: 50%;
          pointer-events: none;
        }
        .o1 {
          width: 300px; height: 300px;
          top: -90px; left: -70px;
          animation: drift 11s ease-in-out infinite;
          background: radial-gradient(circle, rgba(45,212,191,0.12) 0%, transparent 68%);
        }
        .o2 {
          width: 240px; height: 240px;
          bottom: 260px; right: -80px;
          animation: drift 14s ease-in-out infinite reverse;
          background: radial-gradient(circle, rgba(77,232,174,0.08) 0%, transparent 68%);
        }
        .o3 {
          width: 180px; height: 180px;
          top: 240px; right: -30px;
          animation: drift 18s ease-in-out infinite;
          background: radial-gradient(circle, rgba(103,232,249,0.07) 0%, transparent 68%);
        }
        @keyframes drift {
          0%, 100% { transform: translate(0,0) scale(1); }
          33% { transform: translate(7px,-10px) scale(1.04); }
          66% { transform: translate(-5px,7px) scale(0.97); }
        }
      `}</style>
    </div>
  )
}
