import { useNavigate } from 'react-router-dom'
import SpaceHeader from '@/components/layout/SpaceHeader'
import Card from '@/components/ui/Card'
import Insight from '@/components/ui/Insight'
import Pill from '@/components/ui/Pill'
import Button from '@/components/ui/Button'

export default function DecideScreen() {
  const navigate = useNavigate()

  return (
    <div className="flex flex-1 flex-col overflow-hidden min-h-0"
      style={{ background: 'radial-gradient(ellipse at 40% 25%, #001a24 0%, #000a10 55%, #000508 100%)' }}>
      <SpaceHeader title="KA" badge="KA DECIDE" badgeColor="sky" backPath="/" />

      <div className="flex-1 overflow-y-auto px-5 hide-scrollbar min-h-0">
        {/* Header */}
        <div className="flex items-center gap-3 py-4">
          <div className="h-8 w-8 shrink-0 rounded-full flex items-center justify-center"
            style={{ background: 'var(--sky-d)', border: '0.5px solid var(--sky-g)' }}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="7" fill="rgba(24,95,165,0.85)"/>
              <ellipse cx="6" cy="5.5" rx="3" ry="2.2" fill="rgba(255,255,255,0.28)"/>
            </svg>
          </div>
          <div>
            <div className="text-[15px] text-[var(--t1)]">Changer de voiture ?</div>
            <div className="mt-[2px] text-[12px] text-[var(--t3)]">Basé sur 14 mois de données</div>
          </div>
        </div>

        {/* Cost overview */}
        <div className="grid grid-cols-2 gap-2 mb-[14px]">
          <Card>
            <div className="text-[9.5px] tracking-[.06em] text-[var(--t4)] mb-[3px]">COÛT / AN</div>
            <div className="text-[19px] font-light text-[var(--t1)]">2 340€</div>
            <div className="mt-[1px] text-[10px] text-[var(--coral)]">+18% vs 2023</div>
          </Card>
          <Card>
            <div className="text-[9.5px] tracking-[.06em] text-[var(--t4)] mb-[3px]">KM</div>
            <div className="text-[19px] font-light text-[var(--t1)]">142k</div>
            <div className="mt-[1px] text-[10px] text-[var(--t4)]">8 ans · Clio IV</div>
          </Card>
        </div>

        {/* Insight */}
        <Insight label="CE QUE KA OBSERVE" color="sky">
          Deux réparations en 4 mois — 890€. L'assurance a augmenté de 15%. Le coût dépasse désormais celui d'une occasion récente.
        </Insight>

        {/* Comparison */}
        <div className="mb-4 text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">COMPARAISON</div>
        
        <div className="flex flex-col gap-3 mb-2">
          {/* Option 1 */}
          <div>
            <div className="flex justify-between mb-[5px]">
              <span className="text-[13px] text-[var(--t2)]">Garder la Clio</span>
              <span className="text-[13px] text-[var(--coral)]">2 340€</span>
            </div>
            <div className="h-[5px] rounded-[3px] bg-[var(--g2)] overflow-hidden">
              <div className="h-full rounded-[3px]" style={{ width: '78%', background: 'rgba(208,90,30,0.55)' }} />
            </div>
          </div>

          {/* Option 2 */}
          <div>
            <div className="flex justify-between items-center mb-[5px]">
              <span className="text-[13px] text-[var(--t2)]">Occasion récente</span>
              <div className="flex items-center gap-[6px]">
                <Pill color="sky" className="text-[9.5px] !px-[7px] !py-[2px]">conseillé</Pill>
                <span className="text-[13px] text-[var(--sky)]">3 200€</span>
              </div>
            </div>
            <div className="h-[5px] rounded-[3px] bg-[var(--g2)] overflow-hidden">
              <div className="h-full rounded-[3px]" style={{ width: '100%', background: 'rgba(150,200,245,0.60)' }} />
            </div>
            <div className="mt-1 text-[10.5px] text-[var(--t4)]">1ère année · baisse à ~1 800€ ensuite</div>
          </div>

          {/* Option 3 */}
          <div>
            <div className="flex justify-between mb-[5px]">
              <span className="text-[13px] text-[var(--t2)]">Sans voiture</span>
              <span className="text-[13px] text-[var(--life)]">1 100€</span>
            </div>
            <div className="h-[5px] rounded-[3px] bg-[var(--g2)] overflow-hidden">
              <div className="h-full rounded-[3px]" style={{ width: '36%', background: 'rgba(61,219,160,0.45)' }} />
            </div>
          </div>
        </div>
      </div>

      <div className="flex gap-2 px-5 pb-[calc(14px+var(--sb))] pt-[10px] shrink-0">
        <Button color="sky">🔍 Explorer les occasions</Button>
        <Button color="ghost">Analyser sans voiture</Button>
      </div>
    </div>
  )
}