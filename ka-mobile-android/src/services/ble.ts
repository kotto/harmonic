/**
 * BLE Service — Bluetooth Low Energy pour capteurs médicaux
 * Compatible : ECG, Oxymètre SpO2, Thermomètre, Tensiomètre
 *
 * Nécessite : @capacitor-community/bluetooth-le
 * Permissions Android : BLUETOOTH_SCAN, BLUETOOTH_CONNECT, ACCESS_FINE_LOCATION
 */

import { isNative } from './native'

/* ── Types ── */

export interface BLESensorReading {
  type: 'ecg' | 'spo2' | 'temperature' | 'blood_pressure' | 'heart_rate'
  value: number
  unit: string
  timestamp: number
  deviceName: string
}

export interface BLEDevice {
  deviceId: string
  name: string
  rssi: number
  type: string
  connected: boolean
}

export type BLEStatus = 'idle' | 'scanning' | 'connecting' | 'connected' | 'error'

/* ── Capteurs supportés ── */

const KNOWN_SENSORS: Record<string, { type: BLESensorReading['type']; serviceUUID: string; charUUID: string }> = {
  // Standard BLE Health services
  'heart_rate': { type: 'heart_rate', serviceUUID: '0000180d-0000-1000-8000-00805f9b34fb', charUUID: '00002a37-0000-1000-8000-00805f9b34fb' },
  'blood_pressure': { type: 'blood_pressure', serviceUUID: '00001810-0000-1000-8000-00805f9b34fb', charUUID: '00002a35-0000-1000-8000-00805f9b34fb' },
  'temperature': { type: 'temperature', serviceUUID: '00001809-0000-1000-8000-00805f9b34fb', charUUID: '00002a1c-0000-1000-8000-00805f9b34fb' },
  'pulse_oximeter': { type: 'spo2', serviceUUID: '00001822-0000-1000-8000-00805f9b34fb', charUUID: '00002a5f-0000-1000-8000-00805f9b34fb' },
}

/* ── Service state ── */

let bleStatus: BLEStatus = 'idle'
let connectedDevices: BLEDevice[] = []
let listeners: Array<(reading: BLESensorReading) => void> = []
let statusListeners: Array<(status: BLEStatus) => void> = []

/* ── Initialisation ── */

let BleClient: any = null

async function ensureBLE(): Promise<boolean> {
  if (!isNative()) return false

  try {
    // Dynamic import — only available on native
    // @ts-ignore — package installed at build time
    const mod = await import(/* @vite-ignore */ '@capacitor-community/bluetooth-le')
    BleClient = mod.BleClient
    await BleClient.initialize()
    return true
  } catch (e) {
    console.warn('[BLE] Plugin non disponible:', e)
    return false
  }
}

/* ── Scan ── */

export async function scanForSensors(timeoutMs = 10000): Promise<BLEDevice[]> {
  if (!await ensureBLE()) {
    console.warn('[BLE] Mode web — scan impossible')
    return []
  }

  bleStatus = 'scanning'
  notifyStatus()
  const found: BLEDevice[] = []

  try {
    await BleClient.requestLEScan(
      { services: Object.values(KNOWN_SENSORS).map(s => s.serviceUUID) },
      (result: any) => {
        const name = result.device?.name || 'Inconnu'
        const sensorType = Object.entries(KNOWN_SENSORS).find(([key]) =>
          name.toLowerCase().includes(key.replace('_', ' '))
        )

        found.push({
          deviceId: result.device.deviceId,
          name,
          rssi: result.rssi || -100,
          type: sensorType?.[0] || 'unknown',
          connected: false,
        })
      }
    )

    // Arrêter après timeout
    setTimeout(async () => {
      await BleClient.stopLEScan()
      bleStatus = 'idle'
      notifyStatus()
    }, timeoutMs)

  } catch (e) {
    bleStatus = 'error'
    notifyStatus()
    console.error('[BLE] Erreur scan:', e)
  }

  return found
}

/* ── Connexion ── */

export async function connectSensor(deviceId: string): Promise<boolean> {
  if (!BleClient) return false

  bleStatus = 'connecting'
  notifyStatus()

  try {
    await BleClient.connect(deviceId, (id: string) => {
      // Déconnexion callback
      connectedDevices = connectedDevices.map(d =>
        d.deviceId === id ? { ...d, connected: false } : d
      )
      bleStatus = 'idle'
      notifyStatus()
    })

    const device = connectedDevices.find(d => d.deviceId === deviceId)
    if (device) device.connected = true

    bleStatus = 'connected'
    notifyStatus()
    return true
  } catch (e) {
    bleStatus = 'error'
    notifyStatus()
    console.error('[BLE] Erreur connexion:', e)
    return false
  }
}

/* ── Lecture capteur ── */

export async function startNotifications(
  deviceId: string,
  sensorType: string,
): Promise<void> {
  if (!BleClient) return

  const sensor = KNOWN_SENSORS[sensorType]
  if (!sensor) throw new Error(`Capteur inconnu: ${sensorType}`)

  await BleClient.startNotifications(
    deviceId,
    sensor.serviceUUID,
    sensor.charUUID,
    (value: DataView) => {
      const reading = parseReading(sensorType, value, deviceId)
      if (reading) notifyListeners(reading)
    }
  )
}

export async function stopNotifications(
  deviceId: string,
  sensorType: string,
): Promise<void> {
  if (!BleClient) return
  const sensor = KNOWN_SENSORS[sensorType]
  if (!sensor) return
  await BleClient.stopNotifications(deviceId, sensor.serviceUUID, sensor.charUUID)
}

/* ── Parsing ── */

function parseReading(type: string, data: DataView, deviceId: string): BLESensorReading | null {
  const device = connectedDevices.find(d => d.deviceId === deviceId)
  const deviceName = device?.name || 'Capteur'

  try {
    switch (type) {
      case 'heart_rate': {
        const flags = data.getUint8(0)
        const hr = (flags & 0x01) ? data.getUint16(1, true) : data.getUint8(1)
        return { type: 'heart_rate', value: hr, unit: 'bpm', timestamp: Date.now(), deviceName }
      }
      case 'temperature': {
        const temp = data.getFloat32(1, true)
        return { type: 'temperature', value: temp, unit: '°C', timestamp: Date.now(), deviceName }
      }
      case 'spo2': {
        const spo2 = data.getFloat32(1, true)
        return { type: 'spo2', value: spo2, unit: '%', timestamp: Date.now(), deviceName }
      }
      case 'blood_pressure': {
        const systolic = data.getFloat32(1, true)
        const diastolic = data.getFloat32(3, true)
        return { type: 'blood_pressure', value: systolic / diastolic, unit: 'ratio', timestamp: Date.now(), deviceName }
      }
      default:
        return null
    }
  } catch (e) {
    console.error('[BLE] Erreur parsing:', e)
    return null
  }
}

/* ── Listeners ── */

export function onSensorReading(fn: (reading: BLESensorReading) => void): () => void {
  listeners.push(fn)
  return () => { listeners = listeners.filter(l => l !== fn) }
}

export function onStatusChange(fn: (status: BLEStatus) => void): () => void {
  statusListeners.push(fn)
  return () => { statusListeners = statusListeners.filter(l => l !== fn) }
}

function notifyListeners(reading: BLESensorReading) {
  listeners.forEach(fn => fn(reading))
}

function notifyStatus() {
  statusListeners.forEach(fn => fn(bleStatus))
}

/* ── Getters ── */

export function getStatus(): BLEStatus { return bleStatus }
export function getConnectedDevices(): BLEDevice[] { return connectedDevices }
export function getKnownSensors() { return KNOWN_SENSORS }
export function isBLEAvailable(): boolean { return isNative() && BleClient !== null }

/* ── Simulation (mode web / dev) ── */

export function simulateReading(type: BLESensorReading['type']): BLESensorReading {
  const base: Omit<BLESensorReading, 'type' | 'value' | 'unit'> = {
    timestamp: Date.now(),
    deviceName: 'Simulateur KA',
  }

  switch (type) {
    case 'heart_rate':
      return { ...base, type, value: 62 + Math.random() * 15, unit: 'bpm' }
    case 'spo2':
      return { ...base, type, value: 96 + Math.random() * 3, unit: '%' }
    case 'temperature':
      return { ...base, type, value: 36.4 + Math.random() * 0.8, unit: '°C' }
    case 'blood_pressure':
      return { ...base, type, value: 1.5 + Math.random() * 0.15, unit: 'ratio' }
    default:
      return { ...base, type, value: 70, unit: 'bpm' }
  }
}
