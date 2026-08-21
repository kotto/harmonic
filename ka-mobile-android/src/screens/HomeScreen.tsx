import { useNavigate } from 'react-router-dom'

export default function HomeScreen() {
  const navigate = useNavigate()

  return (
    <div className="flex flex-1 flex-col items-center justify-between overflow-hidden min-h-0">
      {/* Sphere */}
      <div className="relative mt-8 shrink-0 cursor-pointer" onClick={() => navigate('/messages')} role="button" aria-label="Ouvrir KA">
        <div className="absolute -inset-4 rounded-full border border-[var(--b3)] opacity-0 pointer-events-none"
          style={{ animation: 'pring 2.6s ease-out infinite' }} />
        <div className="absolute -inset-8 rounded-full border border-[var(--b2)] opacity-0 pointer-events-none"
          style={{ animation: 'pring 2.6s ease-out 0.65s infinite' }} />
        <svg width="120" height="120" viewBox="0 0 120 120" role="img" aria-label="Sphère KA">
          <defs>
            <radialGradient id="sg" cx="37%" cy="33%" r="65%">
              <stop offset="0%" stopColor="#66f7ff" stopOpacity=".96"/>
              <stop offset="52%" stopColor="#00F2FF" stopOpacity=".92"/>
              <stop offset="100%" stopColor="#006b70" stopOpacity=".86"/>
            </radialGradient>
            <radialGradient id="ig" cx="40%" cy="35%" r="52%">
              <stop offset="0%" stopColor="#b0fbff" stopOpacity=".55"/>
              <stop offset="100%" stopColor="#00F2FF" stopOpacity="0"/>
            </radialGradient>
            <filter id="sf"><feGaussianBlur stdDeviation="3"/></filter>
          </defs>
          <ellipse cx="60" cy="62" rx="50" ry="49" fill="var(--soul-d)" filter="url(#sf)"/>
          <circle cx="60" cy="60" r="46" fill="url(#sg)"/>
          <ellipse cx="47" cy="40" rx="18" ry="13" fill="url(#ig)"/>
          <path d="M60 16C82 18 98 36 100 60" stroke="var(--t4)" strokeWidth="1.2" fill="none"/>
        </svg>
      </div>

      {/* Greeting */}
      <div className="mt-6 shrink-0 text-center">
        <h1 className="text-[30px] font-light tracking-[-.025em] text-[var(--t1)] hud-title">Bonjour</h1>
        <p className="mt-[6px] text-[14px] text-[var(--t3)]">Que souhaitez-vous faire ?</p>
      </div>

      {/* Intent bar */}
      <div
        className="mt-[26px] flex w-[264px] shrink-0 cursor-pointer items-center gap-[10px] px-4 py-3"
        style={{
          background: 'var(--g1)',
          border: 'var(--bw, 0.5px) solid var(--b2)',
          borderRadius: 'var(--r-pill, 26px)',
        }}
        onClick={() => navigate('/messages')}
        role="button"
        aria-label="Exprimer une intention"
      >
        <div className="h-8 w-8 shrink-0 rounded-full bg-[var(--soul-d)] flex items-center justify-center"
          style={{ border: '0.5px solid var(--soul-g)', animation: 'breathe 4s ease-in-out infinite' }}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" fill="var(--soul)"/>
            <ellipse cx="6" cy="5.5" rx="3" ry="2.2" fill="rgba(255,255,255,0.28)"/>
          </svg>
        </div>
        <span className="text-[14px] text-[var(--t4)]">Intention…</span>
      </div>

      {/* Quick actions — HUD angular style */}
      <div className="mt-auto flex w-full justify-center gap-[14px] px-[22px] shrink-0">
        <button className="qa" onClick={() => navigate('/call')} aria-label="Appel">
          <div className="qa__i" style={{ background: 'var(--life-d)', borderColor: 'var(--life-g)' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M5 5.5C5 4.7 5.7 4 6.5 4h3l1.5 4-2.5 1.5c1 2 2.8 3.8 4.8 4.8L15 12l4 1.5V17c0 .8-.7 1.5-1.5 1.5C9.5 19 5 10.5 5 5.5Z" fill="var(--life)"/>
            </svg>
          </div>
          <span>Appel</span>
        </button>

        <button className="qa" onClick={() => navigate('/messages')} aria-label="Message">
          <div className="qa__i" style={{ background: 'var(--soul-d)', borderColor: 'var(--soul-g)' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M4 4h16a1 1 0 011 1v11a1 1 0 01-1 1H7l-4 4V5a1 1 0 011-1z" fill="var(--soul)"/>
            </svg>
          </div>
          <span>Message</span>
        </button>

        <button className="qa" onClick={() => navigate('/memory')} aria-label="Souvenir">
          <div className="qa__i" style={{ background: 'var(--sky-d)', borderColor: 'var(--sky-g)' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle cx="12" cy="12" r="9" stroke="var(--soul)" strokeWidth="1.5" fill="none"/>
              <path d="M12 8v4l3 3" stroke="var(--soul)" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
            </svg>
          </div>
          <span>Mémoire</span>
        </button>

        <button className="qa" onClick={() => navigate('/relation')} aria-label="Relations">
          <div className="qa__i" style={{ background: 'var(--rose-d)', borderColor: 'var(--rose-g)' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle cx="9" cy="8" r="3.5" stroke="var(--amber)" strokeWidth="1.5" fill="none"/>
              <path d="M2 20c0-3.3 3.1-6 7-6s7 2.7 7 6" stroke="var(--amber)" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
            </svg>
          </div>
          <span>Réseau</span>
        </button>
      </div>

      <div style={{ height: '16px', flexShrink: 0 }} />

      <style>{`
        .qa {
          display: flex; flex-direction: column; align-items: center; gap: 7px;
          cursor: pointer; border: none; background: none;
        }
        .qa span {
          font-size: 10px; color: var(--t4); letter-spacing: 0.08em;
          text-transform: uppercase;
        }
        .qa__i {
          width: 56px; height: 56px;
          border-radius: var(--r-avatar, 50%);
          display: flex; align-items: center; justify-content: center;
          border: var(--bw, 0.5px) solid transparent;
          transition: transform 0.15s cubic-bezier(.34,1.56,.64,1);
        }
        .qa__i:active { transform: scale(0.88); }

        /* V2 override: angular quick actions */
        [data-theme="v2"] .qa__i {
          border-radius: 2px !important;
          border-width: 1px !important;
        }
        [data-theme="v2"] .qa span {
          font-size: 9px;
          color: rgba(0, 242, 255, 0.55);
        }
        [data-theme="v2"] .qa__i svg {
          opacity: 0.85;
        }
      `}</style>
    </div>
  )
}