import { useNavigate } from 'react-router-dom'
import SpaceHeader from '@/components/layout/SpaceHeader'
import Insight from '@/components/ui/Insight'
import Card from '@/components/ui/Card'
import Stat from '@/components/ui/Stat'
import Button from '@/components/ui/Button'
import type { Stat as StatType } from '@/types'

export default function RelationScreen() {
  const navigate = useNavigate()

  const stats: StatType[] = [
    { label: 'appels', value: 23, color: 'default' },
    { label: 'messages', value: 340, color: 'default' },
    { label: 'photos', value: 156, color: 'default' },
    { label: 'voyages', value: 4, color: 'default' },
  ]

  return (
    <div className="flex flex-1 flex-col overflow-hidden min-h-0"
      style={{ background: 'linear-gradient(160deg, #281420 0%, #0a0a14 100%)' }}>
      <SpaceHeader title="KA" badge="KA RELATION" badgeColor="rose" backPath="/" />

      <div className="flex-1 overflow-y-auto px-5 hide-scrollbar min-h-0">
        {/* Profile */}
        <div className="flex flex-col items-center py-5">
          <div className="relative mb-3">
            <div className="absolute -inset-2 rounded-full border border-[var(--rose-g)]"
              style={{ animation: 'breathe 4s ease-in-out infinite' }} />
            <div className="w-16 h-16 rounded-full bg-[var(--rose-d)] flex items-center justify-center text-[22px] text-[var(--rose)]">
              S
            </div>
          </div>
          <div className="text-[19px] text-[var(--t1)]">Sophie</div>
          <div className="mt-[2px] text-[12px] text-[var(--t3)]">Amie proche · depuis 2019</div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-[6px] mb-3">
          {stats.map((s, i) => <Stat key={i} stat={s} />)}
        </div>

        {/* Insight */}
        <Insight label="KA REMARQUE" color="rose">
          Vous n'avez pas parlé depuis 9 jours — c'est inhabituel. Votre rythme moyen est tous les 2 jours.
        </Insight>

        {/* Shared memories */}
        <div className="mb-2 text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">SOUVENIRS PARTAGÉS</div>
        <div className="grid grid-cols-4 gap-[6px] pb-[14px]">
          {['linear-gradient(135deg,#3a3050,#241d35)', 'linear-gradient(135deg,#2d3a3a,#1d2828)', 'linear-gradient(135deg,#3a2d35,#281d22)'].map((g, i) => (
            <div key={i} className="aspect-square rounded-[10px] cursor-pointer"
              style={{ background: g }} />
          ))}
          <div className="aspect-square rounded-[10px] bg-[var(--g1)] flex items-center justify-center text-[12px] font-medium text-[var(--t3)] cursor-pointer">
            +153
          </div>
        </div>

        {/* Last message */}
        <Card>
          <div className="flex items-center gap-[10px]">
            <div className="w-7 h-7 rounded-full bg-[var(--rose-d)] flex items-center justify-center text-[11px] text-[var(--rose)] shrink-0">
              S
            </div>
            <div>
              <div className="text-[12.5px] text-[var(--t2)]">"On garde ce resto en tête !"</div>
              <div className="text-[11px] text-[var(--t4)]">il y a 9 jours</div>
            </div>
          </div>
        </Card>
      </div>

      <div className="flex gap-2 px-5 pb-[calc(14px+var(--sb))] pt-[10px] shrink-0">
        <Button color="rose" onClick={() => navigate('/call')}>📞 Appeler</Button>
        <Button color="ghost" onClick={() => navigate('/messages')}>Écrire</Button>
      </div>
    </div>
  )
}