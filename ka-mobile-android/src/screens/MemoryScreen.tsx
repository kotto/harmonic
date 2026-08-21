import { useNavigate } from 'react-router-dom'
import SpaceHeader from '@/components/layout/SpaceHeader'
import Pill from '@/components/ui/Pill'
import Insight from '@/components/ui/Insight'
import Button from '@/components/ui/Button'

const photos = [
  'linear-gradient(135deg,#3a3050,#241d35)',
  'linear-gradient(135deg,#2d3a3a,#1d2828)',
  'linear-gradient(135deg,#3a2d35,#281d22)',
]

export default function MemoryScreen() {
  const navigate = useNavigate()

  return (
    <div className="flex flex-1 flex-col overflow-hidden min-h-0"
      style={{ background: 'linear-gradient(160deg, #1e1630 0%, #0a0a14 100%)' }}>
      <SpaceHeader title="KA" badge="KA MEMORY" backPath="/" />

      <div className="flex-1 overflow-y-auto px-5 hide-scrollbar min-h-0">
        {/* Memory header */}
        <div className="flex items-center gap-3 py-4">
          <div className="h-8 w-8 shrink-0 rounded-full bg-[var(--soul-d)] flex items-center justify-center"
            style={{ border: '0.5px solid var(--soul-g)', animation: 'breathe 4s ease-in-out infinite' }}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="7" fill="rgba(45,212,191,0.85)"/>
              <ellipse cx="6" cy="5.5" rx="3" ry="2.2" fill="rgba(255,255,255,0.28)"/>
            </svg>
          </div>
          <div>
            <div className="text-[15px] text-[var(--t1)]">Rome avec Sophie</div>
            <div className="mt-[2px] text-[12px] text-[var(--t3)]">14–17 sept 2024 · 4 jours</div>
          </div>
        </div>

        {/* Pills */}
        <div className="flex gap-[7px] mb-[14px]">
          <Pill color="life">📷 47 photos</Pill>
          <Pill color="soul">💬 12 messages</Pill>
          <Pill color="wisdom">📍 Rome</Pill>
        </div>

        {/* Photos grid */}
        <div className="grid grid-cols-4 gap-[6px] pb-[14px]">
          {photos.map((g, i) => (
            <div key={i} className="aspect-square rounded-[10px] cursor-pointer transition-transform active:scale-[.94]"
              style={{ background: g }} />
          ))}
          <div className="aspect-square rounded-[10px] bg-[var(--g1)] flex items-center justify-center text-[12px] font-medium text-[var(--t3)] cursor-pointer">
            +44
          </div>
        </div>

        {/* Insight */}
        <Insight label="DERNIER MESSAGE" color="soul">
          <div>"On garde ce resto en tête pour la prochaine fois"</div>
          <div className="mt-1 text-[11px] text-[var(--t4)]">16 sept · avec 3 photos</div>
        </Insight>

        {/* Timeline */}
        <div className="mb-4 text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">CHRONOLOGIE</div>
        <div className="relative pl-[22px] flex flex-col gap-0 mb-4">
          <div className="absolute left-[6px] top-1 bottom-1 w-[1px] bg-[var(--b2)]" />
          
          <div className="relative">
            <div className="absolute -left-[22px] top-[5px] w-[7px] h-[7px] rounded-full bg-[var(--life)]" />
            <div className="text-[13px] text-[var(--t2)]">Colisée — 23 photos</div>
            <div className="text-[11px] text-[var(--t4)]">14 sept · 10h12</div>
          </div>
          <div className="relative mt-[10px]">
            <div className="absolute -left-[22px] top-[5px] w-[7px] h-[7px] rounded-full bg-[var(--soul)]" />
            <div className="text-[13px] text-[var(--t2)]">Message envoyé à Marie</div>
            <div className="text-[11px] text-[var(--t4)]">15 sept · "Regarde où on est !"</div>
          </div>
          <div className="relative mt-[10px]">
            <div className="absolute -left-[22px] top-[5px] w-[7px] h-[7px] rounded-full bg-[var(--wisdom)]" />
            <div className="text-[13px] text-[var(--t2)]">Trastevere — dîner, 18 photos</div>
            <div className="text-[11px] text-[var(--t4)]">16 sept · 20h41</div>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="flex gap-2 px-5 pb-[calc(14px+var(--sb))] pt-[10px] shrink-0">
        <Button color="soul" onClick={() => {}}>📷 Créer un album</Button>
        <Button color="ghost" onClick={() => navigate('/messages')}>Partager</Button>
      </div>
    </div>
  )
}