import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import SpaceHeader from '@/components/layout/SpaceHeader'
import Button from '@/components/ui/Button'
import Pill from '@/components/ui/Pill'
import Card from '@/components/ui/Card'

interface Hologram {
  id: string
  name: string
  description: string
  category: string
  size: string
  installed?: boolean
}

const MOCK_HOLOGRAMS: Hologram[] = [
  { id: 'med', name: 'Médecine Générale', description: 'Diagnostics, pathologies, médicaments', category: 'Santé', size: '4.2 Mo', installed: true },
  { id: 'math', name: 'Mathématiques', description: 'Calculs, théorèmes, formules', category: 'Sciences', size: '2.1 Mo', installed: true },
  { id: 'astro', name: 'Astronomie', description: 'Astres, planètes, cosmologie', category: 'Sciences', size: '6.8 Mo' },
  { id: 'cuisine', name: 'Cuisine & Nutrition', description: 'Recettes, régimes, aliments', category: 'Quotidien', size: '3.4 Mo' },
  { id: 'droit', name: 'Droit & Législation', description: 'Lois, codes, jurisprudence', category: 'Société', size: '8.5 Mo' },
  { id: 'musique', name: 'Musique & Harmonie', description: 'Théorie musicale, accords, composition', category: 'Arts', size: '5.1 Mo' },
  { id: 'tech', name: 'Technologies', description: 'Programmation, IA, réseaux', category: 'Sciences', size: '7.3 Mo' },
  { id: 'psy', name: 'Psychologie', description: 'Comportement, émotions, cognition', category: 'Santé', size: '4.9 Mo' },
]

type Filter = 'all' | 'installed' | 'available'

export default function HologramScreen() {
  const navigate = useNavigate()
  const [filter, setFilter] = useState<Filter>('all')
  const [specialization, setSpecialization] = useState('')
  const [status, setStatus] = useState<string | null>(null)
  const [holograms, setHolograms] = useState(MOCK_HOLOGRAMS)

  const filtered = holograms.filter(h => {
    if (filter === 'installed') return h.installed
    if (filter === 'available') return !h.installed
    return true
  })

  const handleSpecialize = () => {
    if (!specialization.trim()) return
    setStatus(`🎯 Spécialisation « ${specialization} » en cours…`)
    setTimeout(() => {
      const newHolo: Hologram = {
        id: 'spec-' + Date.now(),
        name: specialization,
        description: 'Hologramme personnalisé',
        category: 'Personnalisé',
        size: '—',
        installed: true,
      }
      setHolograms(prev => [newHolo, ...prev])
      setStatus(`✅ Hologramme « ${specialization} » créé avec succès`)
      setSpecialization('')
    }, 2000)
  }

  const handleInstall = (id: string) => {
    setHolograms(prev =>
      prev.map(h => (h.id === id ? { ...h, installed: true } : h))
    )
    setStatus(`📥 Installation de ${holograms.find(h => h.id === id)?.name}…`)
    setTimeout(() => setStatus(`✅ ${holograms.find(h => h.id === id)?.name} installé`), 1500)
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden min-h-0"
      style={{ background: 'linear-gradient(160deg, #1e1430 0%, #0a0a14 100%)' }}>
      <SpaceHeader title="KA" badge="HOLOGRAMMES" badgeColor="wisdom" backPath="/" />

      <div className="flex-1 overflow-y-auto px-5 hide-scrollbar min-h-0">
        <div className="text-center text-[12px] text-[var(--t4)] py-2">
          Savoirs spécialisés téléchargeables.
        </div>

        {/* Status */}
        {status && (
          <div className="text-center text-[12px] px-[10px] py-[10px] mb-[10px] rounded-[10px]"
            style={{ background: 'rgba(120,200,255,0.08)', color: 'var(--sky)' }}>
            {status}
          </div>
        )}

        {/* Specialization */}
        <Card>
          <div className="text-[12px] font-bold text-[var(--wisdom)] mb-2">🎯 VOS CENTRES D'INTÉRÊT</div>
          <div className="flex gap-[6px]">
            <input
              value={specialization}
              onChange={e => setSpecialization(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSpecialize()}
              placeholder="ex : diabète, nutrition, astronomie"
              className="flex-1 px-3 py-[10px] rounded-[12px] text-[13px] outline-none"
              style={{ background: 'var(--g1)', border: '0.5px solid var(--b2)', color: 'var(--t1)' }}
            />
            <button
              onClick={handleSpecialize}
              className="rounded-[26px] px-[14px] py-[10px] text-[13px] cursor-pointer"
              style={{ background: 'var(--wisdom)', color: '#fff', border: 'none' }}
            >
              Créer
            </button>
          </div>
        </Card>

        {/* Filters */}
        <div className="flex gap-[6px] mb-3 flex-wrap justify-center">
          {(['all', 'installed', 'available'] as Filter[]).map(f => {
            const labels = { all: '🌟 Tous', installed: '✅ Installés', available: '📥 Disponibles' }
            return (
              <span
                key={f}
                className={`inline-flex items-center rounded-[20px] px-[10px] py-[4px] text-[10.5px] font-medium border-[0.5px] cursor-pointer ${
                  filter === f
                    ? f === 'all'
                      ? 'bg-[var(--life-d)] border-[var(--life-g)] text-[var(--life)]'
                      : 'bg-[var(--soul-d)] border-[var(--soul-g)] text-[var(--soul-l)]'
                    : 'bg-[var(--g1)] border-[var(--b2)] text-[var(--t3)]'
                }`}
                onClick={() => setFilter(f)}
              >
                {labels[f]}
              </span>
            )
          })}
        </div>

        {/* Hologram list */}
        <div className="flex flex-col gap-2 pb-4">
          {filtered.map(h => (
            <div
              key={h.id}
              className="rounded-[14px] p-3"
              style={{ background: h.installed ? 'rgba(77,232,174,0.04)' : 'var(--g1)', border: '0.5px solid var(--b2)' }}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[13px] font-medium text-[var(--t1)]">{h.name}</span>
                    {h.installed && <span className="text-[11px] text-[var(--life)]">✅</span>}
                  </div>
                  <div className="text-[11px] text-[var(--t4)] mt-[2px]">{h.description}</div>
                  <div className="flex gap-2 mt-1">
                    <Pill color="sky">{h.category}</Pill>
                    <span className="text-[10px] text-[var(--t4)] self-center">{h.size}</span>
                  </div>
                </div>
                {!h.installed && (
                  <button
                    onClick={() => handleInstall(h.id)}
                    className="shrink-0 ml-2 rounded-[26px] px-[12px] py-[6px] text-[11px] cursor-pointer border-[0.5px]"
                    style={{ background: 'var(--soul-d)', borderColor: 'var(--soul-g)', color: 'var(--soul-l)' }}
                  >
                    📥
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-2 px-5 pb-[calc(14px+var(--sb))] pt-[10px] shrink-0">
        <Button color="ghost" onClick={() => navigate('/')}>Fermer</Button>
      </div>
    </div>
  )
}