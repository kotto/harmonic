import { useNavigate } from 'react-router-dom'
import SpaceHeader from '@/components/layout/SpaceHeader'
import Insight from '@/components/ui/Insight'
import Button from '@/components/ui/Button'

export default function PrepareScreen() {
  const navigate = useNavigate()

  return (
    <div className="flex flex-1 flex-col overflow-hidden min-h-0"
      style={{ background: 'linear-gradient(160deg, #1e1a30 0%, #0a0a14 100%)' }}>
      <SpaceHeader title="KA" badge="KA PREPARE" backPath="/" />

      <div className="flex-1 overflow-y-auto px-5 hide-scrollbar min-h-0">
        {/* Header */}
        <div className="flex items-center gap-3 py-4">
          <div className="h-8 w-8 shrink-0 rounded-full flex items-center justify-center"
            style={{ background: 'rgba(83,74,183,0.22)', border: '0.5px solid rgba(127,119,221,0.32)' }}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="7" fill="rgba(83,74,183,0.85)"/>
              <ellipse cx="6" cy="5.5" rx="3" ry="2.2" fill="rgba(255,255,255,0.28)"/>
            </svg>
          </div>
          <div>
            <div className="text-[15px] text-[var(--t1)]">Revue produit Q3</div>
            <div className="mt-[2px] text-[12px] text-[var(--t3)]">Demain · 10h00 — 11h00</div>
          </div>
        </div>

        {/* Participants */}
        <div className="mb-4 text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">PARTICIPANTS</div>
        <div className="flex gap-[10px] mb-[14px]">
          {[
            { initials: 'S', name: 'Sophie', bg: 'var(--soul-d)', border: 'var(--soul-g)', color: 'var(--soul-l)' },
            { initials: 'M', name: 'Marc', bg: 'var(--life-d)', border: 'var(--life-g)', color: 'var(--life)' },
            { initials: 'L', name: 'Léa', bg: 'var(--wisdom-d)', border: 'var(--wisdom-g)', color: 'var(--wisdom)' },
            { initials: '+2', name: 'autres', bg: 'var(--g1)', border: 'var(--b2)', color: 'var(--t3)', dashed: true },
          ].map((p, i) => (
            <div key={i} className="flex flex-col items-center gap-1">
              <div className="w-9 h-9 rounded-full flex items-center justify-center text-[13px] font-medium"
                style={{
                  background: p.bg,
                  border: p.dashed ? `0.5px dashed ${p.border}` : `0.5px solid ${p.border}`,
                  color: p.color,
                }}>
                {p.initials}
              </div>
              <span className="text-[10px] text-[var(--t4)]">{p.name}</span>
            </div>
          ))}
        </div>

        {/* Briefing */}
        <Insight label="BRIEFING KA" color="soul">
          Sophie a relancé deux fois sur les chiffres de rétention. Marc attend la maquette finale. Point sensible : le retard de livraison signalé jeudi.
        </Insight>

        {/* Agenda */}
        <div className="mb-4 text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">ORDRE DU JOUR</div>
        <div className="relative pl-[22px] flex flex-col gap-0 mb-[14px]">
          <div className="absolute left-[6px] top-1 bottom-1 w-[1px] bg-[var(--b2)]" />
          <div className="relative">
            <div className="absolute -left-[22px] top-[5px] w-[7px] h-[7px] rounded-full bg-[var(--soul)]" />
            <div className="text-[13px] text-[var(--t2)]">Chiffres de rétention — Sophie</div>
          </div>
          <div className="relative mt-[8px]">
            <div className="absolute -left-[22px] top-[5px] w-[7px] h-[7px] rounded-full bg-[var(--soul)]" />
            <div className="text-[13px] text-[var(--t2)]">Validation budget maquette</div>
          </div>
          <div className="relative mt-[8px]">
            <div className="absolute -left-[22px] top-[5px] w-[7px] h-[7px] rounded-full bg-[#f07040]" />
            <div className="text-[13px] text-[var(--t2)]">
              Retard livraison <span className="text-[11px] text-[#f07040]">⚠ point sensible</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex gap-2 px-5 pb-[calc(14px+var(--sb))] pt-[10px] shrink-0">
        <Button color="soul">📤 Partager le briefing</Button>
        <Button color="ghost">Ouvrir doc</Button>
      </div>
    </div>
  )
}