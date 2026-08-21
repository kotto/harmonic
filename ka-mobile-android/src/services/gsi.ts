/**
 * GSI — Golden Health Index
 * Indice de Santé Doré basé sur la Théorie Harmonique Universelle
 *
 * 5 oscillateurs physiologiques comparés à φ = 1.618...
 * GSI = moyenne des écarts normalisés par rapport à φ
 */

export const PHI = 1.618033988749895
export const INV_PHI = 1 / PHI // 0.618...

/* ── Oscillateur definitions ── */

export interface OscillatorReading {
  id: string
  label: string
  value: number
  unit: string
  target: number
  /** Ecart absolu normalisé (0 = parfait, 1 = très écarté) */
  delta: number
  /** Statut : bon | modéré | écarté */
  status: 'good' | 'moderate' | 'warning'
  /** Source de la mesure */
  source: 'sensor' | 'manual' | 'estimated'
}

export interface GSIResult {
  /** Score global GSI entre 0 et 100 */
  score: number
  /** Label qualitatif */
  label: string
  /** Couleur d'affichage */
  color: string
  /** Oscillateurs individuels */
  oscillators: OscillatorReading[]
  /** Timestamp de la mesure */
  timestamp: number
}

/* ── Constantes physiologiques ── */

interface OscillatorSpec {
  id: string
  label: string
  unit: string
  target: number
  tolerance: number // écart max acceptable (normalisé)
}

export const OSCILLATORS: OscillatorSpec[] = [
  { id: 'sd',    label: 'S/D',      unit: '',    target: INV_PHI, tolerance: 0.15 },
  { id: 'lfhf',  label: 'LF/HF',    unit: '',    target: PHI,     tolerance: 0.25 },
  { id: 'ie',    label: 'I/E',      unit: '',    target: INV_PHI, tolerance: 0.15 },
  { id: 'beta',  label: 'β/α',      unit: '',    target: PHI,     tolerance: 0.20 },
  { id: 'temp',  label: 'Temp',     unit: '°C',  target: 37.0,    tolerance: 0.05 },
]

/* ── Calcul d'un oscillateur ── */

function computeDelta(value: number, target: number, tolerance: number): number {
  const rawDelta = Math.abs(value - target) / target
  return Math.min(rawDelta / tolerance, 1) // normalisé 0→1
}

function getStatus(delta: number): OscillatorReading['status'] {
  if (delta <= 0.33) return 'good'
  if (delta <= 0.66) return 'moderate'
  return 'warning'
}

/* ── Calcul GSI ── */

export interface GSIInput {
  /** Systole / Diastole (ex: 120/80 → 0.667) */
  systole?: number
  diastole?: number
  /** LF/HF ratio (variabilité cardiaque) */
  lfHf?: number
  /** Inspiration / Expiration (ex: 4s/6s → 0.667) */
  inspiration?: number
  expiration?: number
  /** Beta/Alpha ratio (EEG ou estimation) */
  betaAlpha?: number
  /** Température corporelle */
  temperature?: number
  /** Sources disponibles */
  source?: 'sensor' | 'manual' | 'estimated'
}

export function calculateGSI(input: GSIInput): GSIResult {
  const source = input.source || 'estimated'
  const oscillators: OscillatorReading[] = []

  // S/D
  if (input.systole !== undefined && input.diastole !== undefined && input.diastole > 0) {
    const ratio = input.systole / input.diastole / 2 // normalisé pour comparer à 1/φ
    const spec = OSCILLATORS[0]
    const delta = computeDelta(ratio, spec.target, spec.tolerance)
    oscillators.push({
      id: spec.id, label: spec.label, value: ratio, unit: spec.unit,
      target: spec.target, delta, status: getStatus(delta), source,
    })
  }

  // LF/HF
  if (input.lfHf !== undefined) {
    const spec = OSCILLATORS[1]
    const delta = computeDelta(input.lfHf, spec.target, spec.tolerance)
    oscillators.push({
      id: spec.id, label: spec.label, value: input.lfHf, unit: spec.unit,
      target: spec.target, delta, status: getStatus(delta), source,
    })
  }

  // I/E
  if (input.inspiration !== undefined && input.expiration !== undefined && input.expiration > 0) {
    const ratio = input.inspiration / input.expiration
    const spec = OSCILLATORS[2]
    const delta = computeDelta(ratio, spec.target, spec.tolerance)
    oscillators.push({
      id: spec.id, label: spec.label, value: ratio, unit: spec.unit,
      target: spec.target, delta, status: getStatus(delta), source,
    })
  }

  // β/α
  if (input.betaAlpha !== undefined) {
    const spec = OSCILLATORS[3]
    const delta = computeDelta(input.betaAlpha, spec.target, spec.tolerance)
    oscillators.push({
      id: spec.id, label: spec.label, value: input.betaAlpha, unit: spec.unit,
      target: spec.target, delta, status: getStatus(delta), source,
    })
  }

  // Température
  if (input.temperature !== undefined) {
    const spec = OSCILLATORS[4]
    const rawDelta = Math.abs(input.temperature - spec.target) / spec.target
    const delta = Math.min(rawDelta / spec.tolerance, 1)
    oscillators.push({
      id: spec.id, label: spec.label, value: input.temperature, unit: spec.unit,
      target: spec.target, delta, status: getStatus(delta), source,
    })
  }

  // Score global
  if (oscillators.length === 0) {
    return { score: -1, label: 'Aucune donnée', color: '#f07040', oscillators: [], timestamp: Date.now() }
  }

  const avgDelta = oscillators.reduce((sum, o) => sum + o.delta, 0) / oscillators.length
  const score = Math.round((1 - avgDelta) * 100)

  let label: string
  let color: string
  if (score >= 80) { label = 'Harmonie'; color = '#4de8ae' }
  else if (score >= 60) { label = 'Équilibre'; color = '#2dd4bf' }
  else if (score >= 40) { label = 'Tension'; color = '#f5cc6a' }
  else { label = 'Désaccord'; color = '#f07040' }

  return { score, label, color, oscillators, timestamp: Date.now() }
}

/* ── Simulation (données de test) ── */

export function simulateGSI(): GSIResult {
  return calculateGSI({
    systole: 118 + Math.random() * 6,
    diastole: 76 + Math.random() * 5,
    lfHf: 1.4 + Math.random() * 0.5,
    inspiration: 3.8 + Math.random() * 0.6,
    expiration: 6.0 + Math.random() * 0.8,
    betaAlpha: 1.5 + Math.random() * 0.3,
    temperature: 36.6 + Math.random() * 0.8,
    source: 'estimated',
  })
}

/* ── Helpers ── */

export function statusColor(status: OscillatorReading['status']): string {
  switch (status) {
    case 'good': return '#4de8ae'
    case 'moderate': return '#f5cc6a'
    case 'warning': return '#f07040'
  }
}

export function formatOscillatorValue(o: OscillatorReading): string {
  if (o.id === 'temp') return o.value.toFixed(1) + '°'
  if (o.id === 'sd' || o.id === 'ie') return o.value.toFixed(3)
  return o.value.toFixed(2)
}
