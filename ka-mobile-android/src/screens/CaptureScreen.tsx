import { useNavigate } from 'react-router-dom'
import SpaceHeader from '@/components/layout/SpaceHeader'
import Card from '@/components/ui/Card'
import Pill from '@/components/ui/Pill'
import Button from '@/components/ui/Button'

export default function CaptureScreen() {
  const navigate = useNavigate()

  const waves = Array.from({ length: 18 }, (_, i) => ({
    h: 3 + Math.random() * 16,
    dur: 0.35 + Math.random() * 0.5,
    delay: Math.random() * 0.4,
  }))

  return (
    <div className="flex flex-1 flex-col overflow-hidden min-h-0"
      style={{ background: 'linear-gradient(160deg, #142820 0%, #0a0a14 100%)' }}>
      <SpaceHeader title="KA" badge="KA CAPTURE" badgeColor="life" backPath="/" />

      <div className="flex-1 overflow-y-auto px-5 hide-scrollbar min-h-0 flex flex-col items-center">
        {/* Mic icon */}
        <div className="relative my-5">
          <div className="absolute -inset-[10px] rounded-full border border-[var(--life-g)]"
            style={{ animation: 'breathe 3s ease-in-out infinite' }} />
          <div className="w-14 h-14 rounded-full bg-[var(--life-d)] flex items-center justify-center"
            style={{ border: '0.5px solid var(--life-g)' }}>
            <div className="w-7 h-7 rounded-full" style={{ background: 'rgba(61,219,160,0.85)' }} />
          </div>
        </div>

        {/* Wave visualization */}
        <div className="flex gap-[3px] items-center h-[22px] mb-[18px]">
          {waves.map((w, i) => (
            <div
              key={i}
              className="w-[2.5px] rounded-[2px]"
              style={{
                height: w.h + 'px',
                background: 'rgba(77,232,174,0.70)',
                animation: `wave ${w.dur}s ease-in-out infinite alternate ${w.delay}s`,
              }}
            />
          ))}
        </div>

        {/* Transcription */}
        <Card raised>
          <div className="mb-1 text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">
            CE QUE KA A ENTENDU
          </div>
          <div className="text-[13.5px] leading-[1.55] text-[var(--t2)]">
            "Une appli qui propose une recette en fonction de ce qui reste dans le frigo, avec une photo plutôt qu'une liste"
          </div>
        </Card>

        {/* Structured tags */}
        <div className="self-start mb-2 text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">
          STRUCTURÉ EN
        </div>
        <Card>
          <div className="flex items-center gap-[10px]">
            <Pill color="life">Concept</Pill>
            <span className="text-[12.5px] text-[var(--t2)]">Reconnaissance d'ingrédients par photo</span>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-[10px]">
            <Pill color="soul">Cible</Pill>
            <span className="text-[12.5px] text-[var(--t2)]">Anti-gaspillage alimentaire</span>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-[10px]">
            <Pill color="wisdom">Lié à</Pill>
            <span className="text-[12.5px] text-[var(--t2)]">2 idées similaires du mois dernier</span>
          </div>
        </Card>
      </div>

      <div className="flex gap-2 px-5 pb-[calc(14px+var(--sb))] pt-[10px] shrink-0">
        <Button color="life">→ Développer</Button>
        <Button color="ghost">Classer</Button>
      </div>

      <style>{`
        @keyframes wave { 0%,100% { height: 3px; } 50% { height: var(--wh, 18px); } }
      `}</style>
    </div>
  )
}