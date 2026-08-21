import { useNavigate } from 'react-router-dom'
import SpaceHeader from '@/components/layout/SpaceHeader'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'

export default function JourneyScreen() {
  const navigate = useNavigate()

  return (
    <div className="flex flex-1 flex-col overflow-hidden min-h-0"
      style={{ background: 'linear-gradient(160deg, #281e0c 0%, #0a0a14 100%)' }}>
      <SpaceHeader title="KA" badge="KA JOURNEY" badgeColor="wisdom" backPath="/" />

      <div className="flex-1 overflow-y-auto px-5 hide-scrollbar min-h-0">
        {/* Header */}
        <div className="flex items-center gap-3 py-4">
          <div className="h-8 w-8 shrink-0 rounded-full flex items-center justify-center"
            style={{ background: 'var(--wisdom-d)', border: '0.5px solid var(--wisdom-g)' }}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="7" fill="rgba(186,117,23,0.85)"/>
              <ellipse cx="6" cy="5.5" rx="3" ry="2.2" fill="rgba(255,255,255,0.28)"/>
            </svg>
          </div>
          <div>
            <div className="text-[15px] text-[var(--t1)]">Tokyo</div>
            <div className="mt-[2px] text-[12px] text-[var(--t3)]">8 — 15 oct · 7 jours</div>
          </div>
        </div>

        {/* Weather & Flight */}
        <div className="grid grid-cols-2 gap-2 mb-[14px]">
          <Card>
            <div className="text-[9.5px] tracking-[.06em] text-[var(--t4)] mb-[3px]">MÉTÉO</div>
            <div className="text-[19px] font-light text-[var(--t1)]">
              19°<span className="text-[11px] text-[var(--sky)]"> nuageux</span>
            </div>
          </Card>
          <Card style={{ borderColor: 'rgba(240,192,96,0.2)' }}>
            <div className="text-[9.5px] tracking-[.06em] text-[var(--t4)] mb-[3px]">VOL</div>
            <div className="text-[13px] text-[var(--t1)]">CDG → HND</div>
            <div className="text-[10.5px] text-[var(--wisdom)]">dès 612 €</div>
          </Card>
        </div>

        {/* Itinerary */}
        <div className="mb-4 text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">ITINÉRAIRE</div>
        <div className="relative pl-[22px] flex flex-col gap-0 mb-[14px]">
          <div className="absolute left-[6px] top-1 bottom-1 w-[1px] bg-[var(--b2)]" />
          <div className="relative">
            <div className="absolute -left-[22px] top-[5px] w-[7px] h-[7px] rounded-full bg-[var(--wisdom)]" />
            <div className="text-[14px] text-[var(--t2)]">Shibuya · Shinjuku</div>
            <div className="text-[11.5px] text-[var(--t4)]">Jours 1–2 · arrivée, immersion urbaine</div>
          </div>
          <div className="relative mt-[10px]">
            <div className="absolute -left-[22px] top-[5px] w-[7px] h-[7px] rounded-full bg-[var(--life)]" />
            <div className="text-[14px] text-[var(--t2)]">Kyoto · excursion</div>
            <div className="text-[11.5px] text-[var(--t4)]">Jours 3–4 · shinkansen 2h14</div>
          </div>
          <div className="relative mt-[10px]">
            <div className="absolute -left-[22px] top-[5px] w-[7px] h-[7px] rounded-full bg-[var(--soul)]" />
            <div className="text-[14px] text-[var(--t2)]">Asakusa · retour calme</div>
            <div className="text-[11.5px] text-[var(--t4)]">Jours 5–7 · temples, marché</div>
          </div>
        </div>

        {/* Translation hint */}
        <Card>
          <div className="flex items-center gap-[10px]">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <path d="M2 4h7M5 2v2M3 7c1 1.5 3 2.5 4 2.5" stroke="rgba(175,169,236,0.6)" strokeWidth="1" strokeLinecap="round"/>
              <path d="M9 9l2-5 2 5M10 7.5h2" stroke="rgba(93,202,165,0.6)" strokeWidth="1" strokeLinecap="round"/>
            </svg>
            <span className="text-[12px] text-[var(--t3)]">Traduction japonais ↔ français activée</span>
          </div>
        </Card>
      </div>

      <div className="flex gap-2 px-5 pb-[calc(14px+var(--sb))] pt-[10px] shrink-0">
        <Button color="wisdom">✈ Tout réserver</Button>
        <Button color="ghost">Modifier</Button>
      </div>
    </div>
  )
}