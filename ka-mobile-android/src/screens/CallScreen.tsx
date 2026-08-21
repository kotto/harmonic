import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import SpaceHeader from '@/components/layout/SpaceHeader'

export default function CallScreen() {
  const navigate = useNavigate()
  const [seconds, setSeconds] = useState(0)
  const ivRef = useRef<ReturnType<typeof setInterval>>()

  useEffect(() => {
    setSeconds(0)
    ivRef.current = setInterval(() => {
      setSeconds(s => s + 1)
    }, 1000)
    return () => clearInterval(ivRef.current)
  }, [])

  const fmt = (s: number) => {
    const m = String(Math.floor(s / 60)).padStart(2, '0')
    const sec = String(s % 60).padStart(2, '0')
    return m + ':' + sec
  }

  const waves = Array.from({ length: 22 }, (_, i) => ({
    h: 3 + Math.random() * 22,
    dur: 0.35 + Math.random() * 0.5,
    delay: Math.random() * 0.4,
  }))

  return (
    <div className="flex flex-1 flex-col items-center justify-between overflow-hidden"
      style={{ background: 'linear-gradient(160deg, #061a10 0%, #040e0a 100%)' }}
    >
      <SpaceHeader title="Messages" badge="KA CALL" badgeColor="life" backPath="/messages" />

      {/* Avatar */}
      <div className="relative mt-8">
        <div className="absolute -inset-3 rounded-full border border-[var(--life-g)] opacity-0 pointer-events-none"
          style={{ animation: 'pring 2.5s ease-out infinite' }} />
        <div className="absolute -inset-[26px] rounded-full border border-[var(--life-g)] opacity-0 pointer-events-none"
          style={{ animation: 'pring 2.5s ease-out 0.6s infinite' }} />
        <div className="w-[88px] h-[88px] rounded-full bg-[var(--life-d)] border border-[var(--life-g)] flex items-center justify-center text-[28px] text-[var(--life)]">
          S
        </div>
      </div>

      <div className="text-[28px] font-light text-[var(--t1)] mt-4">Sophie</div>
      <div className="text-[13px] text-[var(--life)] mt-1 tracking-[.04em]">Appel en cours</div>
      <div className="text-[24px] font-light text-[var(--t3)] mt-1 tabular-nums">{fmt(seconds)}</div>

      {/* Wave visualization */}
      <div className="flex gap-[3px] items-center h-[28px] mt-[22px]">
        {waves.map((w, i) => (
          <div
            key={i}
            className="w-[2.5px] rounded-[2px]"
            style={{
              height: w.h + 'px',
              background: 'rgba(77,232,174,0.70)',
              animation: `wave ${w.dur}s ease-in-out infinite alternate ${w.delay}s`,
            }}
          />
        ))}
      </div>

      {/* Controls */}
      <div className="flex gap-[18px] mt-7">
        <div className="ctrl">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M9 9.34A4 4 0 0115.65 16M3 3l18 18" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
          </svg>
          <span>Sourdine</span>
        </div>
        <div className="ctrl">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M11 5L6 9H2v6h4l5 4V5zM15.54 8.46a5 5 0 010 7.07" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
          </svg>
          <span>HP</span>
        </div>
        <div className="ctrl">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <rect x="3" y="3" width="18" height="18" rx="3" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" fill="none"/>
            <path d="M3 9h18M9 3v6" stroke="rgba(255,255,255,0.5)" strokeWidth="1.3" strokeLinecap="round" fill="none"/>
          </svg>
          <span>Clavier</span>
        </div>
      </div>

      {/* End call */}
      <div className="mb-9 w-[68px] h-[68px] rounded-full flex items-center justify-center cursor-pointer transition-all active:scale-[.9]"
        style={{ background: 'rgba(226,75,74,0.22)', border: '1px solid rgba(226,75,74,0.38)' }}
        onClick={() => navigate('/messages')}
        role="button"
      >
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M2.5 16.5C4 14 7 12 12 12s8 2 9.5 4.5l-3 2a1 1 0 01-1.3-.3L16 16a14 14 0 00-8 0l-1.2 2.2a1 1 0 01-1.3.3l-3-2z" fill="rgba(248,160,160,0.92)"/>
        </svg>
      </div>

      <style>{`
        .ctrl {
          width: 52px; height: 52px; border-radius: 50%;
          background: var(--g2); border: 0.5px solid var(--b2);
          display: flex; flex-direction: column; align-items: center; justify-content: center;
          cursor: pointer; gap: 4px; transition: all 0.1s;
        }
        .ctrl:active { background: var(--g3); transform: scale(0.9); }
        .ctrl span { font-size: 10px; color: var(--t3); }
        @keyframes wave { 0%,100% { height: 3px; } 50% { height: var(--wh, 18px); } }
      `}</style>
    </div>
  )
}