/**
 * KA CARE — BLE Manager
 * Connexion aux dispositifs médicaux Bluetooth Low Energy
 * 
 * Compatible avec tous les dispositifs certifiés IEEE 11073
 * (tensiomètres, oxymètres, thermomètres, balances, glucomètres)
 * 
 * Usage:
 *   import { quickMeasure, BLE_SERVICES } from './ble_manager.js';
 *   const result = await quickMeasure('blood_pressure');
 *   // → { systolic: 138, diastolic: 88, pulse: 72, unit: 'mmHg', ... }
 */

// ═══════════════════════════════════════════════════════════════
// PROFILS GATT STANDARD (IEEE 11073)
// ═══════════════════════════════════════════════════════════════

const BLE_SERVICES = {
  blood_pressure: {
    uuid: 0x1810,
    characteristic: 0x2A35,
    name: 'Tensiomètre',
    icon: '🩺',
    parser: parseBloodPressure,
  },
  pulse_oximeter: {
    uuid: 0x1822,
    characteristic: 0x2A5E,
    name: 'Oxymètre',
    icon: '🫁',
    parser: parsePulseOximeter,
  },
  thermometer: {
    uuid: 0x1809,
    characteristic: 0x2A1C,
    name: 'Thermomètre',
    icon: '🌡️',
    parser: parseThermometer,
  },
  weight_scale: {
    uuid: 0x181D,
    characteristic: 0x2A9D,
    name: 'Balance',
    icon: '⚖️',
    parser: parseWeightScale,
  },
  glucose: {
    uuid: 0x1808,
    characteristic: 0x2A18,
    name: 'Glucomètre',
    icon: '🩸',
    parser: parseGlucose,
  },
};

// ═══════════════════════════════════════════════════════════════
// PARSERS IEEE 11073
// ═══════════════════════════════════════════════════════════════

function parseBloodPressure(buffer) {
  const view = new DataView(buffer);
  const flags = view.getUint8(0);
  const unit = (flags & 0x01) ? 'kPa' : 'mmHg';
  const systolic = view.getUint16(1, true) / 10;
  const diastolic = view.getUint16(3, true) / 10;
  const map = view.getUint16(5, true) / 10;
  let pulse = null;
  if (flags & 0x40) pulse = view.getUint16(7, true) / 10;
  return { systolic, diastolic, map, pulse, unit };
}

function parsePulseOximeter(buffer) {
  const view = new DataView(buffer);
  const flags = view.getUint8(0);
  const spO2 = view.getUint16(1, true) / 100;
  const pulseRate = view.getUint16(3, true) / 10;
  return { spO2: Math.round(spO2), pulseRate };
}

function parseThermometer(buffer) {
  const view = new DataView(buffer);
  const flags = view.getUint8(0);
  const unit = (flags & 0x01) ? 'F' : 'C';
  const temp = view.getUint32(1, true) / 1000;
  return { temperature: Math.round(temp * 10) / 10, unit };
}

function parseWeightScale(buffer) {
  const view = new DataView(buffer);
  const flags = view.getUint8(0);
  const unit = (flags & 0x01) ? 'lb' : 'kg';
  const weight = view.getUint16(1, true) / 100;
  let bmi = null, height = null;
  if (flags & 0x02) bmi = view.getUint16(3, true) / 10;
  if (flags & 0x04) height = view.getUint16(5, true) / 100;
  return { weight: Math.round(weight * 10) / 10, bmi, height, unit };
}

function parseGlucose(buffer) {
  const view = new DataView(buffer);
  const flags = view.getUint8(0);
  const unit = (flags & 0x01) ? 'mmol/L' : 'g/L';
  const value = view.getUint16(1, true) / 100;
  const type = (flags & 0x08) ? 'plasma' : 'whole_blood';
  return { glucose: Math.round(value * 10) / 10, unit, type };
}

// ═══════════════════════════════════════════════════════════════
// FONCTIONS PRINCIPALES
// ═══════════════════════════════════════════════════════════════

async function scanDevice(deviceType) {
  if (!navigator.bluetooth) {
    throw new Error('Web Bluetooth non supporté sur ce navigateur');
  }
  const config = BLE_SERVICES[deviceType];
  if (!config) throw new Error(`Type de dispositif inconnu: ${deviceType}`);
  
  try {
    const device = await navigator.bluetooth.requestDevice({
      filters: [{ services: [config.uuid] }],
      optionalServices: [config.uuid],
    });
    return device;
  } catch (e) {
    if (e.name === 'NotFoundError') return null;
    if (e.name === 'SecurityError') throw new Error('Permission Bluetooth refusée');
    throw e;
  }
}

async function readMeasurement(device, deviceType) {
  const config = BLE_SERVICES[deviceType];
  const server = await device.gatt.connect();
  
  try {
    const service = await server.getPrimaryService(config.uuid);
    const characteristic = await service.getCharacteristic(config.characteristic);
    
    let value;
    try {
      value = await characteristic.readValue();
    } catch {
      value = await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error('Timeout')), 15000);
        characteristic.addEventListener('characteristicvaluechanged', (e) => {
          clearTimeout(timeout);
          resolve(e.target.value);
        });
        characteristic.startNotifications();
      });
    }
    
    const result = config.parser(value.buffer);
    result.device_name = device.name || config.name;
    result.device_type = deviceType;
    result.timestamp = Date.now();
    return result;
    
  } finally {
    try { await device.gatt.disconnect(); } catch {}
  }
}

async function quickMeasure(deviceType) {
  const device = await scanDevice(deviceType);
  if (!device) return null;
  return readMeasurement(device, deviceType);
}

async function scanAllAvailable() {
  if (!navigator.bluetooth) return [];
  
  const available = [];
  for (const [type, config] of Object.entries(BLE_SERVICES)) {
    try {
      const device = await navigator.bluetooth.requestDevice({
        filters: [{ services: [config.uuid] }],
        optionalServices: [config.uuid],
      });
      available.push({ type, device, ...config });
      await device.gatt.disconnect();
    } catch {
      // Dispositif non trouvé — continuer
    }
  }
  return available;
}

function isBLESupported() {
  return !!(navigator && navigator.bluetooth);
}

// ═══════════════════════════════════════════════════════════════
// EXPORT
// ═══════════════════════════════════════════════════════════════

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { BLE_SERVICES, scanDevice, readMeasurement, quickMeasure, scanAllAvailable, isBLESupported };
}
