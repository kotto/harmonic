import { useNavigate } from 'react-router-dom'
import { useTheme, type KaTheme } from '@/contexts/ThemeContext'

interface MorePanelProps {
  onClose: () => void
}

export default function MorePanel({ onClose }: MorePanelProps) {
  const navigate = useNavigate()
  const { theme, setTheme } = useTheme()

  const items = [
    { path: '/prepare', emoji: '📋', label: 'Préparer', sub: 'Réunion' },
    { path: '/journey', emoji: '✈️', label: 'Voyage', sub: 'Tokyo' },
    { path: '/relation', emoji: '👤', label: 'Relation', sub: 'Sophie' },
    { path: '/capture', emoji: '💡', label: 'Idée', sub: 'Capturer' },
    { path: '/decide', emoji: '⚖️', label: 'Décision', sub: 'Changer de voiture ?' },
    { path: '/health', emoji: '🫀', label: 'Santé', sub: 'Diagnostic harmonique' },
    { path: '/storage', emoji: '💾', label: 'Espace disque', sub: 'Analyse et optimisation' },
    { path: '/hologram', emoji: '🧠', label: 'Hologrammes', sub: 'Savoirs spécialisés' },
    { path: '/code', emoji: '💻', label: 'Code & Maths', sub: 'Calculs · Algorithmes' },
    { path: '/vitalka', emoji: '🌍', label: 'Vital Ka', sub: 'Santé sociale' },
  ]

  const handleClick = (path: string) => {
    onClose()
    navigate(path)
  }

  return (
    <div
      className="more-panel absolute bottom-0 left-0 right-0 z-20 px-5 pb-[calc(16px+var(--sb))] pt-5"
      style={{
        background: 'linear-gradient(to top, #001520, rgba(0,5,8,0.97))',
        borderTop: '0.5px solid rgba(255,255,255,0.1)',
        backdropFilter: 'blur(40px)',
        maxHeight: '70%',
        overflowY: 'auto',
      }}
    >
      <div className="mb-[14px] text-[9.5px] tracking-[.1em] text-[var(--t4)] flex justify-between items-center">
        <span className="hud-title">AUTRES ESPACES</span>
        <span className="cursor-pointer text-[13px] text-[var(--t3)]" onClick={onClose}>✕</span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {items.map((item) => (
          <div
            key={item.path}
            className="flex cursor-pointer items-center gap-[10px] bg-[var(--g1)] p-3"
            style={{
              borderRadius: 'var(--r-card, 14px)',
              border: 'var(--bw, 0.5px) solid var(--b2)',
            }}
            onClick={() => handleClick(item.path)}
          >
            <span className="text-[18px]">{item.emoji}</span>
            <div>
              <div className="text-[13px] text-[var(--t1)]">{item.label}</div>
              <div className="text-[11px] text-[var(--t4)]">{item.sub}</div>
            </div>
          </div>
        ))}
      </div>

      {/* ── Theme toggle ── */}
      <div
        className="flex items-center justify-between mt-4 px-3 py-[10px] bg-[var(--g1)] cursor-pointer"
        style={{
          borderRadius: 'var(--r-card, 14px)',
          border: 'var(--bw, 0.5px) solid var(--b2)',
        }}
        onClick={() => setTheme(theme === 'ocean' ? 'v2' : 'ocean')}
        role="button"
      >
        <div className="flex items-center gap-2">
          <span className="text-[15px]">{theme === 'v2' ? '🖥️' : '🌊'}</span>
          <div>
            <div className="text-[12px] text-[var(--t1)] hud-title">
              THÈME : {theme === 'v2' ? 'KA MOBILE V2' : 'DEEP OCEAN'}
            </div>
            <div className="text-[10px] text-[var(--t4)]">
              {theme === 'v2' ? 'HUD cyan / ambre · coins angulaires' : 'Teal profond · coins arrondis'}
            </div>
          </div>
        </div>
        <div
          className="w-[36px] h-[20px] rounded-[10px] relative transition-all"
          style={{
            background: theme === 'v2' ? 'var(--soul)' : 'var(--g2)',
            border: '0.5px solid var(--b2)',
          }}
        >
          <div
            className="absolute top-[2px] w-[16px] h-[16px] rounded-full bg-white transition-all"
            style={{
              left: theme === 'v2' ? '18px' : '2px',
              boxShadow: theme === 'v2' ? '0 0 6px rgba(0,242,255,0.5)' : 'none',
            }}
          />
        </div>
      </div>

      <div className="mt-2 text-center">
        <button
          className="bg-none border-none text-[var(--t3)] text-xs cursor-pointer"
          onClick={onClose}
        >
          Fermer
        </button>
      </div>
    </div>
  )
}