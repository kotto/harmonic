import { useNavigate, useLocation } from 'react-router-dom'

const NAV_ITEMS = [
  { path: '/', label: 'Accueil', icon: 'home' },
  { path: '/messages', label: 'Messages', icon: 'messages' },
  { path: '/memory', label: 'Mémoire', icon: 'memory' },
] as const

function NavIcon({ icon, active }: { icon: string; active: boolean }) {
  const c = active ? 'rgba(45,212,191,0.9)' : 'rgba(230,255,250,0.45)'
  const sw = '1.5'

  switch (icon) {
    case 'home':
      return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M3 12L12 4l9 8M5 10v9a1 1 0 001 1h4v-5h4v5h4a1 1 0 001-1v-9" stroke={c} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" fill="none"/>
        </svg>
      )
    case 'messages':
      return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M4 4h16a1 1 0 011 1v11a1 1 0 01-1 1H7l-4 4V5a1 1 0 011-1z" stroke={c} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" fill="none"/>
        </svg>
      )
    case 'memory':
      return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="12" r="9" stroke={c} strokeWidth={sw} fill="none"/>
          <path d="M12 8v4l3 3" stroke={c} strokeWidth={sw} strokeLinecap="round" fill="none"/>
        </svg>
      )
    default:
      return null
  }
}

export default function BottomNav() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <nav className="flex shrink-0 items-center justify-around px-[22px] pb-[calc(10px+var(--sb))] pt-2"
      style={{ background: 'rgba(255,255,255,0.03)', borderTop: '0.5px solid var(--b1)' }}
      aria-label="Navigation principale"
    >
      {NAV_ITEMS.map((item) => {
        const active = location.pathname === item.path
        return (
          <button
            key={item.path}
            onClick={() => navigate(item.path)}
            className="flex flex-col items-center gap-1 cursor-pointer border-none bg-transparent px-2 py-1"
            aria-label={item.label}
          >
            <NavIcon icon={item.icon} active={active} />
            <span
              className="text-[10px] tracking-[.04em] transition-colors duration-150"
              style={{ color: active ? 'var(--soul-l)' : 'var(--t4)' }}
            >
              {item.label}
            </span>
          </button>
        )
      })}

      {/* More button */}
      <button
        className="flex flex-col items-center gap-1 cursor-pointer border-none bg-transparent px-2 py-1"
        aria-label="Plus"
        id="nb-more"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="5" cy="12" r="1.5" fill="rgba(255,255,255,0.45)"/>
          <circle cx="12" cy="12" r="1.5" fill="rgba(255,255,255,0.45)"/>
          <circle cx="19" cy="12" r="1.5" fill="rgba(255,255,255,0.45)"/>
        </svg>
        <span className="text-[10px] tracking-[.04em] text-[var(--t4)]">Plus</span>
      </button>
    </nav>
  )
}