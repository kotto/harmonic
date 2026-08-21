import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Button from '@/components/ui/Button'

const DOMAINS = [
  '🏥 Médecine', '🔬 Sciences', '💻 Technologies', '📚 Littérature',
  '🎨 Arts', '🎵 Musique', '🌿 Nature', '🌍 Géographie',
  '📜 Histoire', '💰 Économie', '⚖️ Droit', '🧠 Psychologie',
  '🍳 Cuisine', '🏋️ Sport', '✈️ Voyages', '🧘 Spiritualité',
]

export default function OnboardingScreen() {
  const navigate = useNavigate()
  const [selected, setSelected] = useState<string[]>([])
  const [custom, setCustom] = useState('')
  const [customTags, setCustomTags] = useState<string[]>([])

  const toggleDomain = (d: string) => {
    setSelected(prev =>
      prev.includes(d) ? prev.filter(x => x !== d) : [...prev, d]
    )
  }

  const addCustom = () => {
    const input = document.getElementById('custom-domain-input') as HTMLInputElement
    const tag = input?.value?.trim() || custom.trim()
    if (tag && !customTags.includes(tag)) {
      setCustomTags(prev => [...prev, tag])
      setCustom('')
      if (input) input.value = ''
    }
  }

  const handleCustomChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCustom(e.target.value)
  }

  const handleCustomKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addCustom()
    }
  }

  const total = selected.length + customTags.length
  const canContinue = total >= 3

  const handleContinue = () => {
    const user = {
      domains: selected,
      custom: customTags,
      onboarded: true,
    }
    localStorage.setItem('ka_user', JSON.stringify(user))
    navigate('/')
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden min-h-0"
      style={{ background: 'linear-gradient(160deg, #1e1630 0%, #0a0a14 100%)' }}>
      <div className="flex-1 overflow-y-auto px-4 py-5 hide-scrollbar">
        {/* Header */}
        <div className="text-center mb-5">
          <div className="text-[40px] mb-2">🧠</div>
          <div className="text-[18px] font-bold text-[var(--t1)] mb-1">Bienvenue sur KA</div>
          <div className="text-[13px] text-[var(--t2)]">Votre compagnon personnel. Pour commencer, choisissez ce qui vous intéresse.</div>
        </div>

        {/* Domain selector */}
        <div className="mb-2 text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">
          VOS CENTRES D'INTÉRÊT (3-7 recommandés)
        </div>
        <div className="grid grid-cols-2 gap-2 mb-4">
          {DOMAINS.map(d => {
            const active = selected.includes(d)
            return (
              <div
                key={d}
                className={`rounded-[14px] p-3 cursor-pointer transition-all text-[12px] ${
                  active
                    ? 'bg-[var(--soul-d)] text-[var(--soul-l)]'
                    : 'bg-[var(--g1)] text-[var(--t2)]'
                }`}
                style={{ border: active ? '0.5px solid var(--soul-g)' : '0.5px solid var(--b2)' }}
                onClick={() => toggleDomain(d)}
              >
                {d}
              </div>
            )
          })}
        </div>

        {/* Custom domain */}
        <div className="mb-2 text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">✨ DOMAINE PERSONNALISÉ</div>
        <div className="flex gap-[6px] mb-4">
          <input
            id="custom-domain-input"
            value={custom}
            onChange={handleCustomChange}
            onKeyDown={handleCustomKey}
            placeholder="ex: droit congolais, jardinage bio..."
            className="flex-1 px-[14px] py-[10px] rounded-[12px] text-[13px] outline-none"
            style={{ background: 'var(--g1)', border: '0.5px solid var(--b2)', color: 'var(--t1)' }}
          />
          <button
            onClick={(e) => { e.preventDefault(); addCustom(); }}
            onTouchEnd={(e) => { e.preventDefault(); addCustom(); }}
            type="button"
            className="rounded-[26px] px-[14px] py-[10px] text-[13px] cursor-pointer border-[0.5px] active:scale-95 transition-transform"
            style={{ background: 'var(--soul-d)', borderColor: 'var(--soul-g)', color: 'var(--soul-l)' }}
          >
            + Ajouter
          </button>
        </div>

        {/* Custom tags */}
        {customTags.length > 0 && (
          <div className="flex flex-wrap gap-[6px] mb-4">
            {customTags.map(tag => (
              <span
                key={tag}
                className="inline-flex items-center rounded-[20px] px-[10px] py-[4px] text-[10.5px] font-medium border-[0.5px] cursor-pointer"
                style={{ background: 'var(--soul-d)', borderColor: 'var(--soul-g)', color: 'var(--soul-l)' }}
                onClick={() => setCustomTags(prev => prev.filter(t => t !== tag))}
              >
                {tag} ✕
              </span>
            ))}
          </div>
        )}

        {/* Summary */}
        <div className="text-center text-[12px] text-[var(--t4)] mb-4">
          {canContinue
            ? `✅ ${total} centre${total > 1 ? 's' : ''} d'intérêt sélectionnés`
            : `Sélectionnez au moins ${3 - total} centre${3 - total > 1 ? 's' : ''} d'intérêt supplémentaire${3 - total > 1 ? 's' : ''} pour continuer`}
        </div>

        <div className="flex justify-center">
          <button
            onClick={handleContinue}
            className={`rounded-[26px] px-10 py-3 text-[14px] font-medium cursor-pointer transition-all active:scale-[.97] ${
              canContinue ? '' : 'opacity-50 pointer-events-none'
            }`}
            style={{
              background: canContinue ? 'var(--life)' : 'var(--g1)',
              color: canContinue ? '#04210f' : 'var(--t4)',
              border: canContinue ? 'none' : '0.5px solid var(--b2)',
            }}
          >
            🚀 Commencer
          </button>
        </div>
      </div>
    </div>
  )
}