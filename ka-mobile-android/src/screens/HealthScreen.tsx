import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import SpaceHeader from '@/components/layout/SpaceHeader'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'

type BreathProfile = 'resonance' | 'relaxation' | 'energie'

const BREATH_PROFILES: Record<BreathProfile, { in: number; out: number; label: string }> = {
  resonance: { in: 5, out: 5, label: '🌊 Résonance · 6 cycles/min · 0,1 Hz · cohérence φ' },
  relaxation: { in: 4, out: 8, label: '😌 Relaxation · 5 cycles/min' },
  energie: { in: 6, out: 4, label: '⚡ Énergie · 6 cycles/min' },
}

export default function HealthScreen() {
  const navigate = useNavigate()
  const [camActive, setCamActive] = useState(false)
  const [bpm, setBpm] = useState<number | null>(null)
  const [breathActive, setBreathActive] = useState(false)
  const [breathProfile, setBreathProfile] = useState<BreathProfile>('resonance')
  const [breathPhase, setBreathPhase] = useState<'inspire' | 'expire' | 'pause'>('inspire')
  const [breathCycle, setBreathCycle] = useState(0)
  const [breathRunning, setBreathRunning] = useState(false)
  const [symptomes, setSymptomes] = useState('')
  const [fc, setFc] = useState('')
  const [temp, setTemp] = useState('')
  const [sys, setSys] = useState('')
  const [dia, setDia] = useState('')
  const [spo2, setSpo2] = useState('')
  const [age, setAge] = useState('')
  const [diagnostic, setDiagnostic] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleCamStart = () => {
    setCamActive(true)
    // Simulate PPG measurement
    setTimeout(() => {
      const simulatedBpm = 60 + Math.floor(Math.random() * 30)
      setBpm(simulatedBpm)
      setFc(String(simulatedBpm))
    }, 3000)
  }

  const handleCamStop = () => {
    setCamActive(false)
  }

  const handleBreathStart = () => {
    setBreathRunning(true)
    setBreathCycle(0)
    // Start breath simulation
  }

  const handleBreathStop = () => {
    setBreathRunning(false)
  }

  const handleDiagnostic = async () => {
    setLoading(true)
    setDiagnostic(null)
    // Simulate API call
    setTimeout(() => {
      const diag = generateDiagnostic()
      setDiagnostic(diag)
      setLoading(false)
    }, 1500)
  }

  const generateDiagnostic = () => {
    const fcNum = parseInt(fc) || 72
    const spo2Num = parseInt(spo2) || 98
    const tempNum = parseFloat(temp) || 37.0
    const sysNum = parseInt(sys) || 120
    const diaNum = parseInt(dia) || 80
    const ageNum = parseInt(age) || 40

    let result = ''
    if (fcNum > 100 || fcNum < 50) {
      result += '🫀 <b>Fréquence cardiaque anormale</b> — FC=' + fcNum + ' bpm (norme: 50-100). '
    }
    if (sysNum > 140 || diaNum > 90) {
      result += '💉 <b>Tension artérielle élevée</b> — ' + sysNum + '/' + diaNum + ' mmHg. '
    }
    if (spo2Num < 95) {
      result += '🫁 <b>Saturation basse</b> — SpO₂=' + spo2Num + '% (norme: ≥95%). '
    }
    if (tempNum > 38) {
      result += '🌡️ <b>Fièvre</b> — ' + tempNum + '°C. '
    }
    if (!result) {
      result = '✅ <b>Aucune anomalie critique détectée.</b> Les constantes sont dans les normes harmoniques.'
    }
    return result
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden min-h-0"
      style={{ background: 'radial-gradient(ellipse at 40% 25%, #001a2e 0%, #000a10 55%, #000508 100%)' }}>
      <SpaceHeader title="KA" badge="KA SANTÉ" badgeColor="rose" backPath="/" />

      <div className="flex-1 overflow-y-auto px-5 hide-scrollbar min-h-0">
        {/* Header */}
        <div className="text-[11px] tracking-[.05em] text-center mb-[10px] text-[var(--t2)]">
          Diagnostic par résonance harmonique · φ π e √2 √3 √5
        </div>

        {/* PPG Camera */}
        {camActive && (
          <div className="mb-[10px]">
            <div className="relative w-full max-w-[320px] mx-auto rounded-[16px] overflow-hidden bg-black"
              style={{ maxWidth: '320px', aspectRatio: '3/4' }}>
              <div className="w-full h-full bg-gray-900 flex items-center justify-center">
                <div className="text-[32px] font-bold text-white"
                  style={{ textShadow: '0 0 10px rgba(255,107,138,0.8)' }}>
                  {bpm || '--'}
                  <span className="block text-[12px] text-[rgba(255,255,255,0.7)]">BPM</span>
                </div>
              </div>
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80px] h-[100px] border-2 border-[rgba(255,107,138,0.7)] rounded-[20px] pointer-events-none" />
            </div>
            <div className="flex gap-2 justify-center mt-2">
              <button className="btn--ghost text-[11px] px-[14px] py-[6px]" onClick={handleCamStop}>
                ✕ Arrêter
              </button>
              {bpm && (
                <button className="bg-[var(--life)] text-white text-[11px] px-[14px] py-[6px] rounded-[26px]"
                  onClick={() => {}}>
                  ✓ Appliquer FC
                </button>
              )}
            </div>
            <div className="text-center text-[10px] text-[var(--t4)] mt-1">
              Placez votre visage dans le cadre · Restez immobile
            </div>
          </div>
        )}

        {/* Camera button */}
        {!camActive && (
          <div className="text-center mb-[10px]">
            <button className="btn--ghost text-[12px] px-4 py-2 rounded-[26px]"
              onClick={handleCamStart}>
              📸 Mesurer FC par caméra (PPG)
            </button>
          </div>
        )}

        {/* Breathing */}
        <div className="mb-[10px] text-center">
          <button className="btn--ghost text-[12px] px-4 py-2 rounded-[26px]"
            onClick={() => setBreathActive(!breathActive)}>
            🫁 Assistance respiration harmonique
          </button>

          {breathActive && (
            <Card>
              <div className="text-[10px] text-[var(--t4)] mb-[10px]">
                {BREATH_PROFILES[breathProfile].label}
              </div>

              {/* Profile selector */}
              <div className="flex gap-[6px] justify-center mb-[10px]">
                {(['resonance', 'relaxation', 'energie'] as BreathProfile[]).map(p => (
                  <button
                    key={p}
                    className={`text-[10px] px-[10px] py-[5px] rounded-[26px] ${
                      breathProfile === p
                        ? 'bg-[var(--soul-d)] border-[var(--soul-g)] text-[var(--soul-l)]'
                        : 'bg-[var(--g1)] border-[var(--b1)] text-[var(--t3)]'
                    } border-[0.5px]`}
                    onClick={() => setBreathProfile(p)}
                  >
                    {p === 'resonance' ? '🌊 Résonance' : p === 'relaxation' ? '😌 Relaxation' : '⚡ Énergie'}
                  </button>
                ))}
              </div>

              {/* Breath orb */}
              <div className="relative w-[150px] h-[150px] mx-auto mb-[10px]">
                <div className="absolute inset-0 rounded-full border border-dashed border-[var(--b3)]" />
                <div className="absolute inset-0 rounded-full"
                  style={{
                    background: 'radial-gradient(circle at 50% 50%, var(--soul-d), var(--soul-g))',
                    boxShadow: '0 0 40px rgba(45,212,191,0.25)',
                    transform: breathRunning ? (breathPhase === 'inspire' ? 'scale(0.85)' : 'scale(0.65)') : 'scale(0.65)',
                    transition: 'transform ' + BREATH_PROFILES[breathProfile].in + 's ease-in-out',
                  }}
                />
              </div>

              <div className="text-[18px] font-bold text-[var(--soul-l)]">
                {breathRunning ? (breathPhase === 'inspire' ? 'Inspirez…' : 'Expirez…') : 'Prêt'}
              </div>
              <div className="text-[11px] text-[var(--t3)] mt-[2px]">
                cycle {breathCycle} · 0:00
              </div>

              <div className="mt-[10px] flex gap-2 justify-center">
                {!breathRunning ? (
                  <button className="bg-[var(--life)] text-white text-[12px] px-5 py-2 rounded-[26px]"
                    onClick={handleBreathStart}>
                    ▶ Commencer
                  </button>
                ) : (
                  <button className="btn--ghost text-[12px] px-5 py-2 rounded-[26px]"
                    onClick={handleBreathStop}>
                    ■ Arrêter
                  </button>
                )}
              </div>

              <div className="mt-2 text-[10px] text-[var(--t4)] flex gap-4 justify-center">
                <label className="cursor-pointer">
                  <input type="checkbox" defaultChecked className="mr-1 accent-[var(--life)]" /> Voix
                </label>
                <span>FC: <span className="text-[var(--t1)]">{bpm || '--'}</span></span>
                <span>φ: <span className="text-[var(--t1)]">--</span></span>
              </div>
            </Card>
          )}
        </div>

        {/* Symptômes */}
        <div className="mb-[10px]">
          <label className="text-[11px] text-[var(--t4)] block mb-1">
            Symptômes (séparés par des virgules)
          </label>
          <input
            value={symptomes}
            onChange={e => setSymptomes(e.target.value)}
            placeholder="ex: palpitations, anxiete, insomnie"
            className="w-full px-[14px] py-[10px] rounded-[10px] text-[13px] outline-none"
            style={{ background: 'var(--g1)', border: '0.5px solid var(--b2)', color: 'var(--t1)' }}
          />
        </div>

        {/* Vitals grid */}
        <div className="grid grid-cols-2 gap-2 mb-[10px]">
          {[
            { label: 'FC (bpm)', value: fc, set: setFc, placeholder: '72', cam: true },
            { label: 'Temp. (°C)', value: temp, set: setTemp, placeholder: '37.0', step: '0.1' },
            { label: 'Systolique (mmHg)', value: sys, set: setSys, placeholder: '120' },
            { label: 'Diastolique (mmHg)', value: dia, set: setDia, placeholder: '80' },
            { label: 'SpO₂ (%)', value: spo2, set: setSpo2, placeholder: '98' },
            { label: 'Âge', value: age, set: setAge, placeholder: '40' },
          ].map(field => (
            <div key={field.label}>
              <label className="text-[10px] text-[var(--t4)] block mb-[2px]">
                {field.label}
                {field.cam && bpm && <span className="text-[#ff6b8a] ml-1">📸</span>}
              </label>
              <input
                type={field.step ? 'number' : 'number'}
                value={field.value}
                onChange={e => field.set(e.target.value)}
                placeholder={field.placeholder}
                step={field.step}
                className="w-full px-[10px] py-2 rounded-[10px] text-[12px] outline-none"
                style={{ background: 'var(--g1)', border: '0.5px solid var(--b2)', color: 'var(--t1)' }}
              />
            </div>
          ))}
        </div>

        {/* Result */}
        {loading && (
          <div className="text-center py-5">
            <div className="text-[12px] text-[var(--t4)]">Analyse harmonique en cours...</div>
          </div>
        )}

        {diagnostic && (
          <Card raised>
            <div className="text-[12px] leading-[1.6]" dangerouslySetInnerHTML={{ __html: diagnostic }} />
          </Card>
        )}
      </div>

      {/* CTA */}
      <div className="flex gap-2 px-5 pb-[calc(14px+var(--sb))] pt-[10px] shrink-0">
        <button
          onClick={handleDiagnostic}
          className="flex-1 rounded-[26px] px-[13px] py-[13px] text-center text-[13px] font-normal tracking-[.02em] cursor-pointer transition-all active:scale-[.97]"
          style={{ background: 'linear-gradient(135deg,#ff6b8a,#e0486e)', color: '#fff', border: 'none' }}
        >
          🔬 Diagnostiquer
        </button>
        <Button color="ghost" onClick={() => navigate('/')}>Fermer</Button>
      </div>

      <style>{`
        .btn--ghost {
          background: none; border: none;
          color: var(--t3); cursor: pointer;
          transition: all 0.1s;
        }
        .btn--ghost:active { transform: scale(0.95); }
      `}</style>
    </div>
  )
}