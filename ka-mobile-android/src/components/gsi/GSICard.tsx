/**
 * GSICard — Carte principale GSI dans VitalKaScreen
 * Affiche le score GSI, le radar, les oscillateurs et les actions BLE
 */

import { useState, useEffect, useCallback } from 'react'
import { calculateGSI, simulateGSI, statusColor, formatOscillatorValue } from '@/services/gsi'
import type { GSIResult, GSIInput } from '@/services/gsi'
import { isBLEAvailable, onSensorReading, onStatusChange, simulateReading } from '@/services/ble'
import type { BLESensorReading, BLEStatus } from '@/services/ble'
import GSIRadar from './GSIRadar'
import Card from '@/components/ui/Card'

export default function GSICard() {
  const [result, setResult] = useState<GSIResult | null>(null)
  const [bleStatus, setBleStatus] = useState<BLEStatus>('idle')
  const [lastReading, setLastReading] = useState<BLESensorReading | null>(null)
  const [isSimulating, setIsSimulating] = useState(false)

  // Écouter les lectures BLE
  useEffect(() => {
    const unsub = onSensorReading((reading) => {
      setLastReading(reading)
      // Mettre à jour le GSI avec la nouvelle lecture
      setResult(prev => {
        const input: GSIInput = {}
        if (reading.type === 'blood_pressure') {
          // ratio systole/diastole
          input.systole = reading.value * 80
          input.diastole = 80
        }
        if (reading.type === 'heart_rate') {
          input.lfHf = reading.value / 40 // estimation approximative
        }
        if (reading.type === 'temperature') {
          input.temperature = reading.value
        }
        if (reading.type === 'spo2') {
          input.betaAlpha = (100 - reading.value) / 10 // estimation
        }
        const newResult = calculateGSI(input)
        return prev
          ? { ...newResult, oscillators: mergeOscillators(prev.oscillators, newResult.oscillators) }
          : newResult
      })
    })
    return unsub
  }, [])

  // Écouter le statut BLE
  useEffect(() => {
    const unsub = onStatusChange(setBleStatus)
    return unsub
  }, [])

  // Simulation initiale
  useEffect(() => {
    handleSimulate()
  }, [])

  const handleSimulate = useCallback(() => {
    setIsSimulating(true)
    // Simuler une lecture complète
    const sim = simulateGSI()
    setResult(sim)
    setLastReading(simulateReading('heart_rate'))
    setTimeout(() => setIsSimulating(false), 600)
  }, [])

  const handleMeasure = useCallback(() => {
    if (isBLEAvailable()) {
      // TODO: scanner et connecter
      handleSimulate() // fallback
    } else {
      handleSimulate()
    }
  }, [handleSimulate])

  if (!result) return null

  return (
    <div className="mb-4">
      {/* En-tête GSI */}
      <div className="flex items-center justify-between mb-3 px-1">
        <div>
          <div className="text-[11px] tracking-[.1em] text-[var(--teal)] opacity-65">GSI</div>
          <div className="text-[14px] font-medium text-[var(--t1)]">Golden Health Index</div>
        </div>
        <div className="flex items-center gap-2">
          {bleStatus === 'connected' && (
            <div className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 rounded-full bg-[var(--life)] animate-blink" />
              <span className="text-[9px] text-[var(--life)]">BLE</span>
            </div>
          )}
          <div
            className="cursor-pointer rounded-full px-3 py-1.5 text-[11px] font-medium transition-all active:scale-95"
            style={{
              background: 'var(--teal-d)',
              border: '0.5px solid var(--teal-g)',
              color: 'var(--teal-l)',
              opacity: isSimulating ? 0.5 : 1,
            }}
            onClick={handleMeasure}
            role="button"
            aria-label="Mesurer GSI"
          >
            {isSimulating ? '...' : 'Mesurer'}
          </div>
        </div>
      </div>

      {/* Carte principale */}
      <Card raised>
        <div className="flex items-start gap-4">
          {/* Radar */}
          <div className="shrink-0">
            <GSIRadar result={result} size={180} />
          </div>

          {/* Détails */}
          <div className="flex-1 min-w-0">
            {/* Score */}
            <div className="mb-3">
              <div className="text-[28px] font-bold leading-tight" style={{ color: result.color }}>
                {result.score}
              </div>
              <div className="text-[11px] text-[var(--t3)]">{result.label}</div>
            </div>

            {/* Oscillateurs */}
            <div className="space-y-1.5">
              {result.oscillators.map(osc => (
                <div key={osc.id} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-1.5 h-1.5 rounded-full"
                      style={{ backgroundColor: statusColor(osc.status) }}
                    />
                    <span className="text-[11px] text-[var(--t3)]">{osc.label}</span>
                  </div>
                  <span className="text-[11px] font-medium tabular-nums" style={{ color: statusColor(osc.status) }}>
                    {formatOscillatorValue(osc)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Dernière lecture */}
        {lastReading && (
          <div className="mt-3 pt-3 border-t border-[var(--b1)] flex items-center justify-between">
            <span className="text-[10px] text-[var(--t4)]">
              Dernière mesure: {lastReading.deviceName}
            </span>
            <span className="text-[10px] text-[var(--t3)]">
              {lastReading.value.toFixed(lastReading.type === 'temperature' ? 1 : 0)}{lastReading.unit}
            </span>
          </div>
        )}
      </Card>

      {/* Explication */}
      <div className="mt-2 px-1">
        <div className="text-[9px] text-[var(--t4)] leading-relaxed">
          GSI = écart moyen des 5 oscillateurs physiologiques par rapport à φ (nombre d'or).
          Score 100 = harmonie parfaite.
        </div>
      </div>
    </div>
  )
}

/* ── Helpers ── */

function mergeOscillators(
  existing: GSIResult['oscillators'],
  incoming: GSIResult['oscillators'],
): GSIResult['oscillators'] {
  const map = new Map(existing.map(o => [o.id, o]))
  incoming.forEach(o => map.set(o.id, o))
  return Array.from(map.values())
}
