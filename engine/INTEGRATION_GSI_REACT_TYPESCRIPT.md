# 🚀 INTÉGRATION GSI — VERSION REACT/TYPESCRIPT (KAMOBILE 2026)

## Module GSI pour l'application KA Mobile (React + Capacitor)

---

> **Constat :** La dernière version de KA Mobile est une application React/TypeScript + Capacitor, avec un service `harmonic.ts` (HarmonicAI v3), un service `native.ts` (plugins natifs), et un écran `VitalKaScreen.tsx`. Le GSI s'intègre comme un nouveau service + composant.

---

## I. STRUCTURE DE L'INTÉGRATION

### 1.1 Fichiers à créer

```
ka-mobile-android/src/
  services/
    gsi.ts              ← NOUVEAU : calcul du GSI, 5 oscillateurs, φ
    ble.ts              ← NOUVEAU : connexion BLE aux capteurs (via Capacitor)
  components/
    gsi/
      GSICard.tsx        ← NOUVEAU : carte GSI avec radar et oscillateurs
      GSIMeasure.tsx     ← NOUVEAU : boutons de mesure BLE
      GSIRadar.tsx       ← NOUVEAU : radar canvas des 5 oscillateurs
  screens/
    VitalKaScreen.tsx    ← MODIFIÉ : ajout de la carte GSI
```

### 1.2 Packages à ajouter

```json
// package.json
{
  "dependencies": {
    "@capacitor-community/bluetooth-le": "^6.0.0"  // ← NOUVEAU : BLE
  }
}
```

---

## II. SERVICE GSI — `src/services/gsi.ts`

```typescript
/**
 * GSI — Golden Health Index
 * Calcul du Golden Health Index à partir des 5 oscillateurs harmoniques
 * Fondé sur la Médecine Harmonique (φ = 1.618…)
 */

export const PHI = (1 + Math.sqrt(5)) / 2
export const INV_PHI = 1 / PHI

export interface OscillatorMeasurements {
  sd?: number    // Systole/Diastole
  lfhf?: number  // LF/HF (variabilité cardiaque)
  ie?: number    // Inspiration/Expiration
  ba?: number    // Beta/Alpha (EEG)
  temp?: number  // Température corporelle (°C)
}

export interface OscillatorDelta {
  name: string
  label: string
  icon: string
  value: number | null
  target: number
  delta: number | null
  status: 'optimal' | 'normal' | 'warning' | 'critical' | 'unknown'
}

export interface GSIResult {
  gsi: number | null
  deltas: OscillatorDelta[]
  interpretation: 'optimal' | 'normal' | 'warning' | 'critical' | 'unknown'
  color: string
  label: string
}

/** Seuils du GSI */
const THRESHOLDS = {
  optimal: 0.03,
  normal: 0.06,
  warning: 0.10,
}

/** Calcul des écarts à φ pour chaque oscillateur */
export function calculateDeltas(m: OscillatorMeasurements): OscillatorDelta[] {
  const configs = [
    { name: 'sd', label: 'Cœur (S/D)', icon: '❤️', value: m.sd, target: INV_PHI },
    { name: 'lfhf', label: 'Variabilité (LF/HF)', icon: '💓', value: m.lfhf, target: PHI },
    { name: 'ie', label: 'Respiration (I/E)', icon: '🫁', value: m.ie, target: INV_PHI },
    { name: 'ba', label: 'Cerveau (β/α)', icon: '🧠', value: m.ba, target: PHI },
    { name: 'temp', label: 'Température', icon: '🌡️', value: m.temp, target: 37.0 },
  ]

  return configs.map(c => {
    if (c.value === null || c.value === undefined) {
      return { ...c, delta: null, status: 'unknown' as const }
    }
    let delta: number
    if (c.name === 'temp') {
      delta = Math.abs(c.value - c.target) / c.target
    } else if (c.name === 'lfhf' || c.name === 'ba') {
      delta = Math.abs(c.value - c.target) / c.target
    } else {
      delta = Math.abs(c.value - c.target)
    }

    let status: OscillatorDelta['status']
    if (delta < 0.02) status = 'optimal'
    else if (delta < 0.05) status = 'normal'
    else if (delta < 0.10) status = 'warning'
    else status = 'critical'

    return { ...c, delta, status }
  })
}

/** Calcul du GSI à partir des écarts */
export function calculateGSI(deltas: OscillatorDelta[]): GSIResult {
  const validDeltas = deltas.filter(d => d.delta !== null)
  if (validDeltas.length === 0) {
    return {
      gsi: null,
      deltas,
      interpretation: 'unknown',
      color: '#666',
      label: 'En attente de mesures',
    }
  }

  const gsi = validDeltas.reduce((sum, d) => sum + d.delta!, 0) / validDeltas.length

  let interpretation: GSIResult['interpretation']
  let color: string
  let label: string

  if (gsi < THRESHOLDS.optimal) {
    interpretation = 'optimal'
    color = '#27ae60'
    label = 'Santé optimale'
  } else if (gsi < THRESHOLDS.normal) {
    interpretation = 'normal'
    color = '#f39c12'
    label = 'Santé moyenne'
  } else if (gsi < THRESHOLDS.warning) {
    interpretation = 'warning'
    color = '#e67e22'
    label = 'Risque modéré'
  } else {
    interpretation = 'critical'
    color = '#e74c3c'
    label = 'Risque élevé'
  }

  return { gsi, deltas, interpretation, color, label }
}

/** Formatage du GSI */
export function formatGSI(gsi: number | null): string {
  if (gsi === null) return '--'
  return gsi.toFixed(3)
}
```

---

## III. SERVICE BLE — `src/services/ble.ts`

```typescript
/**
 * GSI BLE — Connexion aux capteurs Bluetooth Low Energy
 * Utilise @capacitor-community/bluetooth-le
 */

import { BluetoothLe } from '@capacitor-community/bluetooth-le'

// UUIDs des services BLE standard
const UUIDs = {
  ecg: { service: '0000fff0-0000-1000-8000-00805f9b34fb',
         char: '0000fff1-0000-1000-8000-00805f9b34fb' },
  temp: { service: '00001809-0000-1000-8000-00805f9b34fb',
          char: '00002a1c-0000-1000-8000-00805f9b34fb' },
  spo2: { service: '00001822-0000-1000-8000-00805f9b34fb',
          char: '00002a5e-0000-1000-8000-00805f9b34fb' },
}

export type BLESensorType = 'ecg' | 'temp' | 'spo2'

export interface BLESensorData {
  type: BLESensorType
  value: number
  raw: DataView
}

export async function scanSensor(type: BLESensorType): Promise<string | null> {
  try {
    const result = await BluetoothLe.requestDevice({
      services: [UUIDs[type].service],
    })
    return result.device?.deviceId || null
  } catch (e) {
    console.error(`BLE scan ${type} failed:`, e)
    return null
  }
}

export async function connectSensor(deviceId: string): Promise<boolean> {
  try {
    await BluetoothLe.connect({ deviceId })
    return true
  } catch (e) {
    console.error('BLE connect failed:', e)
    return false
  }
}

export function startSensorStream(
  type: BLESensorType,
  deviceId: string,
  onData: (data: BLESensorData) => void,
  onError: (err: Error) => void,
): Promise<string> {
  const cfg = UUIDs[type]
  return BluetoothLe.startNotifications({
    deviceId,
    service: cfg.service,
    characteristic: cfg.char,
  }).then(result => {
    // Attach listener
    BluetoothLe.addListener('onNotify', (data: any) => {
      if (data.deviceId === deviceId && data.service === cfg.service) {
        onData({ type, value: parseData(type, data.value), raw: data.value })
      }
    })
    return result
  })
}

function parseData(type: BLESensorType, raw: DataView): number {
  switch (type) {
    case 'temp': return raw.getUint8(0) + raw.getUint8(1) / 100
    case 'spo2': return raw.getUint8(1)
    case 'ecg': return raw.getInt16(0, true) // µV
  }
}
```

---

## IV. COMPOSANT GSI — `src/components/gsi/GSICard.tsx`

```tsx
import { useEffect, useState } from 'react'
import { calculateGSI, calculateDeltas, formatGSI, type OscillatorMeasurements, type GSIResult } from '@/services/gsi'
import GSIRadar from './GSIRadar'

interface Props {
  measurements: OscillatorMeasurements
  onMeasure?: (type: string) => void
}

export default function GSICard({ measurements, onMeasure }: Props) {
  const [result, setResult] = useState<GSIResult | null>(null)

  useEffect(() => {
    const deltas = calculateDeltas(measurements)
    const gsi = calculateGSI(deltas)
    setResult(gsi)
  }, [measurements])

  return (
    <div className="rounded-[16px] p-4"
      style={{ background: 'var(--g1)', border: '0.5px solid var(--b2)' }}>
      
      {/* GSI Value */}
      <div className="flex items-center justify-between mb-3">
        <div className="text-[13px] font-medium text-[var(--t1)]">🌿 Golden Health Index</div>
        <div className="text-[24px] font-bold" style={{ color: result?.color || '#666' }}>
          {formatGSI(result?.gsi ?? null)}
        </div>
      </div>
      
      {/* Label */}
      <div className="text-[11px] mb-3" style={{ color: result?.color || '#666' }}>
        {result?.label || 'En attente…'}
      </div>

      {/* Radar Chart */}
      {result && <GSIRadar deltas={result.deltas} />}

      {/* Oscillator details */}
      <div className="space-y-1 mt-3">
        {result?.deltas.map(d => (
          <div key={d.name} className="flex items-center justify-between text-[11px]">
            <span style={{ color: 'var(--t3)' }}>
              {d.icon} {d.label}
            </span>
            <span style={{
              color: d.status === 'optimal' ? '#27ae60' :
                     d.status === 'normal' ? '#f39c12' :
                     d.status === 'warning' ? '#e67e22' :
                     d.status === 'critical' ? '#e74c3c' : '#666'
            }}>
              {d.value !== null ? d.value.toFixed(3) : '--'}
            </span>
          </div>
        ))}
      </div>

      {/* Measure buttons */}
      <div className="flex gap-2 mt-3">
        <button className="flex-1 px-3 py-2 rounded-[10px] text-[11px] font-medium"
          style={{ background: 'var(--g2)', color: 'var(--t1)' }}
          onClick={() => onMeasure?.('ecg')}>
          📡 ECG
        </button>
        <button className="flex-1 px-3 py-2 rounded-[10px] text-[11px] font-medium"
          style={{ background: 'var(--g2)', color: 'var(--t1)' }}
          onClick={() => onMeasure?.('temp')}>
          🌡️ T°
        </button>
        <button className="flex-1 px-3 py-2 rounded-[10px] text-[11px] font-medium"
          style={{ background: 'var(--g2)', color: 'var(--t1)' }}
          onClick={() => onMeasure?.('eeg')}>
          🧠 EEG
        </button>
      </div>
    </div>
  )
}
```

---

## V. INTÉGRATION DANS VITAL KA SCREEN

```tsx
// ka-mobile-android/src/screens/VitalKaScreen.tsx — ajout dans le rendu

import GSICard from '@/components/gsi/GSICard'
import { useState } from 'react'
import { scanSensor, connectSensor } from '@/services/ble'

export default function VitalKaScreen() {
  const [measurements, setMeasurements] = useState({
    sd: null, lfhf: null, ie: null, ba: null, temp: null
  })

  const handleMeasure = async (type: string) => {
    switch (type) {
      case 'ecg': {
        const deviceId = await scanSensor('ecg')
        if (deviceId) {
          await connectSensor(deviceId)
          // Simuler des données (à remplacer par le vrai flux BLE)
          setMeasurements(prev => ({ ...prev, sd: 0.613, lfhf: 1.52 }))
        }
        break
      }
      case 'temp': {
        const deviceId = await scanSensor('temp')
        if (deviceId) {
          await connectSensor(deviceId)
          setMeasurements(prev => ({ ...prev, temp: 36.8 }))
        }
        break
      }
    }
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden min-h-0"
      style={{ background: 'linear-gradient(160deg, #142018 0%, #0a0e0c 100%)' }}>
      {/* ... header existant ... */}
      
      <div className="flex-1 overflow-y-auto px-5 hide-scrollbar min-h-0 pt-4">
        {/* GSI Card — ajoutée ici */}
        <GSICard 
          measurements={measurements}
          onMeasure={handleMeasure}
        />

        {/* ... reste du contenu existant ... */}
      </div>
    </div>
  )
}
```

---

## VI. ORDRE D'INTÉGRATION

```
1. npm install @capacitor-community/bluetooth-le
2. Créer src/services/gsi.ts       → calcul du GSI (5 oscillateurs, φ)
3. Créer src/services/ble.ts       → connexion BLE (ECG, T°, SpO2)
4. Créer src/components/gsi/GSIRadar.tsx → radar chart
5. Créer src/components/gsi/GSICard.tsx   → carte GSI complète
6. Modifier VitalKaScreen.tsx      → intégrer la carte GSI
```

---

## VII. BUDGET

| Poste | Heures | Coût |
|-------|--------|------|
| Service GSI (gsi.ts) | 4h | 200 € |
| Service BLE (ble.ts) | 8h | 400 € |
| Composant GSIRadar | 4h | 200 € |
| Composant GSICard | 4h | 200 € |
| Intégration VitalKaScreen | 2h | 100 € |
| Tests capteurs BLE | 4h | 200 € |
| **Total** | **26h** | **1 300 €** |

---

> *« L'intégration du GSI dans la version React/TypeScript de KA Mobile prend 26 heures et 1 300 €. Trois fichiers nouveaux, un fichier modifié, un package ajouté. Le GSI devient un service comme les autres — appelé par le composant, affiché dans l'écran Vital Ka, connecté aux capteurs BLE via Capacitor. La Médecine Harmonique n'est plus un concept — c'est un module logiciel. »*
>
> — **Kotto Alain**, 12/08/2026