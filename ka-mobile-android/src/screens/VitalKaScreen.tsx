import { useNavigate } from 'react-router-dom'
import Card from '@/components/ui/Card'
import GSICard from '@/components/gsi/GSICard'

export default function VitalKaScreen() {
  const navigate = useNavigate()

  return (
    <div className="flex flex-1 flex-col overflow-hidden min-h-0"
      style={{ background: 'linear-gradient(160deg, #001a1e 0%, #000508 100%)' }}>
      <div className="flex shrink-0 items-center justify-between px-[22px] pt-[14px]">
        <div
          className="cursor-pointer rounded-xl px-2 py-1 text-[13px] text-[var(--t3)] transition-colors active:bg-[var(--g2)]"
          onClick={() => navigate('/')}
          role="button"
        >
          ‹ KA
        </div>
        <div className="text-[11px] tracking-[.08em] text-[var(--teal)] opacity-65">VITAL KA</div>
        <div style={{ width: '48px' }} />
      </div>

      <div className="flex-1 overflow-y-auto px-5 hide-scrollbar min-h-0 pt-4">
        {/* GSI */}
        <GSICard />

        {/* Header */}
        <div className="flex flex-col items-center mb-6">
          <div className="text-4xl mb-2">🌍</div>
          <div className="text-[18px] font-bold text-[var(--t1)]">Vital Ka</div>
          <div className="text-[12px] text-[var(--t4)]">Santé pour tous — Fondation KA</div>
        </div>

        {/* Health wallet */}
        <Card>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-[var(--life-d)] flex items-center justify-center text-lg"
              style={{ border: '0.5px solid var(--life-g)' }}>
              🩺
            </div>
            <div>
              <div className="text-[14px] font-medium text-[var(--t1)]">Portefeuille de soins</div>
              <div className="text-[11px] text-[var(--t4)]">Antécédents, médicaments, allergies</div>
            </div>
          </div>
        </Card>

        {/* Teleconsultation */}
        <Card>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-[var(--teal-d)] flex items-center justify-center text-lg"
              style={{ border: '0.5px solid var(--teal-g)' }}>
              📹
            </div>
            <div>
              <div className="text-[14px] font-medium text-[var(--t1)]">Téléconsultation</div>
              <div className="text-[11px] text-[var(--t4)]">Consultation à distance · Disponible 24/7</div>
            </div>
          </div>
        </Card>

        {/* Social */}
        <Card>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-[var(--rose-d)] flex items-center justify-center text-lg"
              style={{ border: '0.5px solid var(--rose-g)' }}>
              👥
            </div>
            <div>
              <div className="text-[14px] font-medium text-[var(--t1)]">Aide sociale</div>
              <div className="text-[11px] text-[var(--t4)]">Accès aux droits · Aides · Associations</div>
            </div>
          </div>
        </Card>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-2 mt-2 mb-6">
          <div className="p-3 text-center" style={{ borderRadius: 'var(--r-card, 12px)', background: 'var(--g1)', border: 'var(--bw, 0.5px) solid var(--b2)' }}>
            <div className="text-[18px] font-bold text-[var(--life)]">4</div>
            <div className="text-[9px] text-[var(--t4)] mt-1">Consultations</div>
          </div>
          <div className="p-3 text-center" style={{ borderRadius: 'var(--r-card, 12px)', background: 'var(--g1)', border: 'var(--bw, 0.5px) solid var(--b2)' }}>
            <div className="text-[18px] font-bold text-[var(--soul-l)]">12</div>
            <div className="text-[9px] text-[var(--t4)] mt-1">Documents</div>
          </div>
          <div className="p-3 text-center" style={{ borderRadius: 'var(--r-card, 12px)', background: 'var(--g1)', border: 'var(--bw, 0.5px) solid var(--b2)' }}>
            <div className="text-[18px] font-bold text-[var(--wisdom)]">8</div>
            <div className="text-[9px] text-[var(--t4)] mt-1">Rappels</div>
          </div>
        </div>
      </div>
    </div>
  )
}
