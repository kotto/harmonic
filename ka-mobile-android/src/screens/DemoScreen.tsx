import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function DemoScreen() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [result, setResult] = useState<string | null>(null)
  const [bpm, setBpm] = useState<number | null>(null)

  const demoArithmetic = () => {
    // The famous 987654 × 123456 emergence
    const a = 987654n
    const b = 123456n
    const product = a * b
    setResult(`${a} × ${b} = ${product}`)
  }

  const demoPPG = () => {
    // Simulate PPG
    setTimeout(() => {
      const simulated = 60 + Math.floor(Math.random() * 25)
      setBpm(simulated)
    }, 2000)
  }

  const demoDone = () => {
    localStorage.setItem('ka_demo_done', '1')
    navigate('/onboarding')
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden min-h-0"
      style={{ background: 'linear-gradient(160deg, #1e1630 0%, #0a0a14 100%)' }}>
      <div className="flex-1 flex flex-col items-center justify-center px-6 text-center overflow-y-auto">
        {/* Header */}
        <div className="text-5xl mb-3">{step === 1 ? '⚡' : step === 2 ? '🫀' : '🌍'}</div>
        <div className="text-[22px] font-bold text-[var(--t1)] mb-[6px]">KA</div>
        <div className="text-[13px] text-[var(--t4)] mb-6">
          {step === 1
            ? "L'IA qui ne calcule pas — elle émerge."
            : step === 2
            ? "Votre téléphone voit votre cœur."
            : "Votre IA personnelle est prête."}
        </div>

        {/* Step 1: Emergence arithmetic */}
        {step === 1 && (
          <div>
            <div className="text-[12px] text-[var(--t3)] mb-3">
              Mettez votre téléphone en mode avion ✈️ puis tapez :
            </div>
            <div className="rounded-[14px] px-5 py-[14px] mb-[10px] font-mono text-[17px]"
              style={{ background: 'rgba(45,212,191,0.1)', border: '0.5px solid rgba(45,212,191,0.3)', color: 'var(--soul-l)' }}>
              987654 × 123456
            </div>
            <button
              onClick={demoArithmetic}
              className="rounded-[26px] px-7 py-3 text-[13px] cursor-pointer border-[0.5px] mx-auto"
              style={{ background: 'var(--soul-d)', borderColor: 'var(--soul-g)', color: 'var(--soul-l)' }}
            >
              ⚡ Démontrer
            </button>
            {result && (
              <div className="mt-4 text-[14px] font-mono text-[var(--life)]">
                {result}
              </div>
            )}
            {result && (
              <button
                onClick={() => setStep(2)}
                className="mt-4 rounded-[26px] px-6 py-2 text-[12px] cursor-pointer border-[0.5px]"
                style={{ background: 'var(--life-d)', borderColor: 'var(--life-g)', color: 'var(--life)' }}
              >
                ✨ Continuer →
              </button>
            )}
          </div>
        )}

        {/* Step 2: PPG */}
        {step === 2 && (
          <div>
            <div className="text-[12px] text-[var(--t3)] mb-3">
              Maintenant, votre téléphone va voir votre cœur :
            </div>
            {!bpm ? (
              <button
                onClick={demoPPG}
                className="rounded-[26px] px-7 py-3 text-[13px] cursor-pointer border-[0.5px] mx-auto"
                style={{ background: 'var(--life-d)', borderColor: 'var(--life-g)', color: 'var(--life)' }}
              >
                🫀 Démarrer la caméra
              </button>
            ) : (
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <div className="relative w-20 h-20 rounded-full bg-[var(--soul-d)] flex items-center justify-center"
                    style={{ border: '0.5px solid var(--soul-g)', animation: 'pulse 1.2s ease-in-out infinite' }}>
                    <span className="text-2xl text-[var(--soul-l)]">{bpm}</span>
                  </div>
                </div>
                <div className="text-[12px] text-[var(--t2)] mb-1">Fréquence cardiaque</div>
                <div className="text-[10px] text-[var(--t4)] mb-3">
                  {bpm > 80 ? '🤔 Légèrement élevé — respirez profondément' : '✅ Rythme harmonieux'}
                </div>
                <button
                  onClick={() => setStep(3)}
                  className="rounded-[26px] px-6 py-2 text-[12px] cursor-pointer border-[0.5px]"
                  style={{ background: 'var(--soul-d)', borderColor: 'var(--soul-g)', color: 'var(--soul-l)' }}
                >
                  ✨ Continuer →
                </button>
              </div>
            )}
          </div>
        )}

        {/* Step 3: Done */}
        {step === 3 && (
          <div>
            <div className="text-[17px] font-bold text-[var(--t1)] mb-[6px]">Votre IA personnelle est prête.</div>
            <div className="text-[12px] text-[var(--t4)] mb-4">0 GPU · 0 cloud · 100% hors-ligne</div>
            <button
              onClick={demoDone}
              className="rounded-[26px] px-7 py-3 text-[13px] cursor-pointer"
              style={{ background: 'var(--life)', color: '#04210f', border: 'none' }}
            >
              🚀 Commencer
            </button>
          </div>
        )}
      </div>
    </div>
  )
}