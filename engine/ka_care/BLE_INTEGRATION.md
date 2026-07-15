# INTÉGRATION DISPOSITIFS CONNECTÉS — KA CARE
## Architecture BLE pour zones sous-équipées

---

## 1. PÉRIMÈTRE — CE QUE LA CAMÉRA PEUT ET NE PEUT PAS MESURER

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  MESURES SANS DISPOSITIF (caméra seule)                          │
│  ✅ Fréquence cardiaque (PPG facial) — fiable                     │
│  ✅ Fréquence respiratoire (modulation PPG) — fiable              │
│  ✅ HRV SDNN/RMSSD — tendances seulement                          │
│  ⚠ Tension artérielle — TENDANCE uniquement, pas de valeur        │
│  ⚠ Température — estimation indirecte (pattern fébrile)           │
│  ⚠ SpO₂ — estimation imprécise sans double longueur d'onde        │
│                                                                  │
│  MESURES NÉCESSITANT UN DISPOSITIF                               │
│  ❌ Tension artérielle (mmHg) — brassard obligatoire              │
│  ❌ Température (°C) — thermomètre obligatoire                    │
│  ❌ SpO₂ (%) — oxymètre obligatoire                               │
│  ❌ Glycémie (g/L) — glucomètre obligatoire                       │
│  ❌ Poids (kg) — balance obligatoire                              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. DISPOSITIFS RECOMMANDÉS — PAR BUDGET

### Kit Minimal — 35 € (1 dispositif)
```
┌──────────────────────────────────────────────────────────────────┐
│ Tensimètre bras BLE — Xiaomi Mi Smart Blood Pressure Monitor     │
│ → Pression systolique + diastolique + FC                          │
│ → ~25 €, piles AAA, autonomie 6 mois                              │
│ → Justification : la tension est le signe vital le plus critique  │
│   que la caméra ne peut pas mesurer. Hypertension = 1ère cause    │
│   de mortalité cardiovasculaire mondiale.                         │
└──────────────────────────────────────────────────────────────────┘
```

### Kit Standard — 75 € (4 dispositifs)
```
┌──────────────────────────────────────────────────────────────────┐
│ 1. Tensimètre BLE — Xiaomi Mi Smart (25 €)                       │
│ 2. Oxymètre BLE — Wellue O2Ring ou Contec CMS50F (25 €)          │
│ 3. Thermomètre BLE — Kinsa QuickCare (12 €)                      │
│ 4. Balance BLE — Xiaomi Mi Body Composition Scale (18 €)         │
│                                                                  │
│ → Tous fonctionnent sur piles AAA/AA (pas de recharge)            │
│ → BLE standard, pas d'application propriétaire requise            │
│ → Disponibles sur AliExpress, Amazon, pharmacies locales          │
└──────────────────────────────────────────────────────────────────┘
```

### Kit Complet — 130 € (5 dispositifs)
```
┌──────────────────────────────────────────────────────────────────┐
│ Kit Standard +                                                    │
│ 5. Glucomètre BLE — Accu-Chek Guide Me (50 €)                    │
│ → Glycémie en 5 secondes                                         │
│ → Bandelettes : ~15 €/50 tests (coût récurrent)                  │
│ → Justification : dépistage diabète, urgence hypo/hyperglycémie  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. ARCHITECTURE TECHNIQUE

### 3.1 Communication : Web Bluetooth API

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  NAVIGATEUR (Chrome Android)                                     │
│  ┌──────────────────────────────────────────────┐               │
│  │  KA CARE (PWA)                                │               │
│  │  ┌──────────────────────────────────┐        │               │
│  │  │  ble_manager.js                   │        │               │
│  │  │  • scan_devices()                 │        │               │
│  │  │  • connect(device)                │        │               │
│  │  │  • read_measurement(service)      │        │               │
│  │  │  • parse_gatt(value, profile)     │        │               │
│  │  └──────────────────────────────────┘        │               │
│  │         │                                     │               │
│  │         ▼                                     │               │
│  │  Web Bluetooth API                             │               │
│  │  navigator.bluetooth.requestDevice()           │               │
│  └──────────────────────────────────────────────┘               │
│         │                                                        │
│         ▼ BLE (Bluetooth Low Energy)                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │Tensiomètre│ │ Oxymètre │ │Thermomètre│ │ Balance  │           │
│  │  (BLE)   │ │  (BLE)   │ │  (BLE)   │ │  (BLE)   │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 Profils GATT standard utilisés

| Dispositif | Service UUID | Caractéristique | Format |
|-----------|-------------|-----------------|--------|
| Tensiomètre | `0x1810` (Blood Pressure) | `0x2A35` (Blood Pressure Measurement) | IEEE 11073-10407 |
| Oxymètre | `0x1822` (Pulse Oximeter) | `0x2A5E` (Spot-check SpO₂) | IEEE 11073-10404 |
| Thermomètre | `0x1809` (Health Thermometer) | `0x2A1C` (Temperature Measurement) | IEEE 11073-10408 |
| Balance | `0x181D` (Weight Scale) | `0x2A9D` (Weight Measurement) | IEEE 11073-10415 |
| Glucomètre | `0x1808` (Glucose) | `0x2A18` (Glucose Measurement) | IEEE 11073-10413 |

**Avantage clé :** Tous les dispositifs médicaux BLE certifiés utilisent ces profils GATT standardisés (IEEE 11073). KA CARE n'a pas besoin de drivers spécifiques — juste le parser universel.

---

## 4. IMPLÉMENTATION

### 4.1 Module BLE pour KA CARE

```javascript
// ble_manager.js — Module de connexion aux dispositifs médicaux BLE
// Intégration dans KA CARE (ka_care/ble_manager.js)

const BLE_SERVICES = {
  blood_pressure: {
    service: 0x1810,
    characteristic: 0x2A35,
    name: 'Tensiomètre',
    parser: parseBloodPressure,
  },
  pulse_oximeter: {
    service: 0x1822,
    characteristic: 0x2A5E,
    name: 'Oxymètre',
    parser: parsePulseOximeter,
  },
  thermometer: {
    service: 0x1809,
    characteristic: 0x2A1C,
    name: 'Thermomètre',
    parser: parseThermometer,
  },
  weight_scale: {
    service: 0x181D,
    characteristic: 0x2A9D,
    name: 'Balance',
    parser: parseWeightScale,
  },
  glucose: {
    service: 0x1808,
    characteristic: 0x2A18,
    name: 'Glucomètre',
    parser: parseGlucose,
  },
};

// ─── PARSERS IEEE 11073 ───

function parseBloodPressure(buffer) {
  // IEEE 11073-10407 Blood Pressure Measurement
  const view = new DataView(buffer);
  const flags = view.getUint8(0);
  const unit = (flags & 0x01) ? 'kPa' : 'mmHg';
  // Systolic: SFLOAT (2 bytes, little-endian)
  const systolic = view.getUint16(1, true) / 10;
  // Diastolic: SFLOAT (2 bytes)
  const diastolic = view.getUint16(3, true) / 10;
  // Mean arterial pressure: SFLOAT (2 bytes)
  const map = view.getUint16(5, true) / 10;
  // Pulse rate (if present)
  let pulse = null;
  if (flags & 0x40) {
    pulse = view.getUint16(7, true) / 10;
  }
  return { systolic, diastolic, map, pulse, unit };
}

function parsePulseOximeter(buffer) {
  // IEEE 11073-10404 Pulse Oximetry Spot-check
  const view = new DataView(buffer);
  const flags = view.getUint8(0);
  const spO2 = view.getUint16(1, true) / 100;  // en %
  const pulseRate = view.getUint16(3, true) / 10;
  return { spO2, pulseRate };
}

function parseThermometer(buffer) {
  // IEEE 11073-10408 Temperature Measurement
  const view = new DataView(buffer);
  const flags = view.getUint8(0);
  const unit = (flags & 0x01) ? 'F' : 'C';
  const temp = view.getUint32(1, true) / 1000;  // en °C (ou °F)
  const timestamp = (flags & 0x02) ? view.getUint16(5, true) : null;
  return { temperature: temp, unit, timestamp };
}

function parseWeightScale(buffer) {
  // IEEE 11073-10415 Weight Measurement
  const view = new DataView(buffer);
  const flags = view.getUint8(0);
  const unit = (flags & 0x01) ? 'lb' : 'kg';
  const weight = view.getUint16(1, true) / 100;  // en kg (ou lb)
  const bmi = (flags & 0x02) ? view.getUint16(3, true) / 10 : null;
  const height = (flags & 0x04) ? view.getUint16(5, true) / 100 : null;
  return { weight, bmi, height, unit };
}

function parseGlucose(buffer) {
  // IEEE 11073-10413 Glucose Measurement
  const view = new DataView(buffer);
  const flags = view.getUint8(0);
  const unit = (flags & 0x01) ? 'mmol/L' : 'g/L';
  const value = view.getUint16(1, true) / 100;
  const type = (flags & 0x08) ? 'plasma' : 'whole_blood';
  return { glucose: value, unit, type };
}

// ─── FONCTIONS PRINCIPALES ───

async function scanDevices(deviceType) {
  const config = BLE_SERVICES[deviceType];
  if (!config) throw new Error(`Type inconnu: ${deviceType}`);
  
  try {
    const device = await navigator.bluetooth.requestDevice({
      filters: [{ services: [config.service] }],
      optionalServices: [config.service],
    });
    return device;
  } catch (e) {
    if (e.name === 'NotFoundError') return null;
    throw e;
  }
}

async function readMeasurement(device, deviceType) {
  const config = BLE_SERVICES[deviceType];
  const server = await device.gatt.connect();
  const service = await server.getPrimaryService(config.service);
  const characteristic = await service.getCharacteristic(config.characteristic);
  
  // Lire la valeur (certains dispositifs nécessitent une notification)
  let value;
  try {
    value = await characteristic.readValue();
  } catch {
    // Fallback: attendre une notification
    value = await new Promise((resolve) => {
      characteristic.addEventListener('characteristicvaluechanged', (e) => {
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
}

async function quickMeasure(deviceType) {
  const device = await scanDevices(deviceType);
  if (!device) return null;
  try {
    const measurement = await readMeasurement(device, deviceType);
    await device.gatt.disconnect();
    return measurement;
  } catch (e) {
    console.error(`Erreur mesure ${deviceType}:`, e);
    return null;
  }
}
```

### 4.2 Intégration dans l'interface KA CARE

```javascript
// Ajout dans index.html — bouton de scan BLE par dispositif

function addBLEScanButton(fieldId, deviceType, label) {
  const container = document.getElementById(fieldId).parentElement;
  const btn = document.createElement('button');
  btn.className = 'ble-scan-btn';
  btn.textContent = '📡 ' + label;
  btn.onclick = async () => {
    btn.textContent = '⏳ Scan...';
    btn.disabled = true;
    try {
      const result = await quickMeasure(deviceType);
      if (result) {
        fillMeasurement(fieldId, deviceType, result);
        btn.textContent = '✅ ' + label;
        btn.style.background = 'var(--green)';
      } else {
        btn.textContent = '❌ ' + label;
      }
    } catch(e) {
      btn.textContent = '⚠ ' + label;
      console.error(e);
    }
    btn.disabled = false;
  };
  container.appendChild(btn);
}

function fillMeasurement(fieldId, deviceType, result) {
  switch(deviceType) {
    case 'blood_pressure':
      document.getElementById('sante-sys').value = result.systolic;
      document.getElementById('sante-dia').value = result.diastolic;
      if (result.pulse) document.getElementById('sante-fc').value = result.pulse;
      break;
    case 'pulse_oximeter':
      document.getElementById('sante-spo2').value = result.spO2;
      if (result.pulseRate) document.getElementById('sante-fc').value = result.pulseRate;
      break;
    case 'thermometer':
      document.getElementById('sante-temp').value = result.temperature;
      break;
    case 'weight_scale':
      document.getElementById('sante-weight').value = result.weight;
      if (result.bmi) document.getElementById('sante-bmi').value = result.bmi;
      break;
    case 'glucose':
      document.getElementById('sante-glucose').value = result.glucose;
      break;
  }
}

// Initialiser les boutons BLE au chargement
document.addEventListener('DOMContentLoaded', () => {
  if (navigator.bluetooth) {
    addBLEScanButton('sante-sys', 'blood_pressure', 'Tensiomètre');
    addBLEScanButton('sante-spo2', 'pulse_oximeter', 'Oxymètre');
    addBLEScanButton('sante-temp', 'thermometer', 'Thermomètre');
  } else {
    document.getElementById('ble-notice').style.display = 'block';
  }
});
```

---

## 5. MODE DÉGRADÉ — SAISIE MANUELLE

Quand aucun dispositif BLE n'est disponible, l'agent de santé peut :

1. **Mesurer manuellement** avec un tensiomètre manuel + stéthoscope (30 €, pas de BLE)
2. **Saisir la valeur** dans le champ correspondant
3. KA CARE applique la même analyse harmonique

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  AVEC dispositif BLE        │  SANS dispositif BLE               │
│  ──────────────────────     │  ──────────────────                 │
│  📡 Scan → ✅ 138/88       │  Saisie manuelle : [138] / [88]    │
│  Automatique, pas d'erreur  │  L'agent lit le tensiomètre manuel │
│  de saisie                   │  et tape les valeurs               │
│                                                                  │
│  MÊME ANALYSE HARMONIQUE dans les deux cas                       │
│  MÊME VERDICT : RÉFÉRER / TRAITER / SURVEILLER                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. DÉPLOIEMENT — ÉQUIPER UN POSTE DE SANTÉ

### Coût par poste de santé (3 agents)

| Option | Dispositifs | Coût total | Maintenance/an |
|--------|------------|-----------|----------------|
| **Minimale** | 1 tensiomètre BLE | 25 € | 5 € (piles) |
| **Standard** | Tensiomètre + oxymètre + thermomètre + balance | 75 € | 15 € (piles + bandelettes) |
| **Complète** | Standard + glucomètre + 3 téléphones Android Go | 250 € | 50 € |

### Pour un district de 50 postes de santé

```
50 postes × Kit Standard = 50 × 75 € = 3 750 €
+ 3 téléphones/poste (50 €/unité) = 7 500 €
+ Formation (1 jour/poste) = 2 500 €
─────────────────────────────────────────
TOTAL : ~13 750 € pour équiper un district entier
```

À comparer au budget santé annuel d'un district type en Afrique subsaharienne : 500 000 € à 2 000 000 €. **KA CARE + dispositifs représente moins de 1 % de ce budget.**

---

## 7. FOURNISSEURS RECOMMANDÉS

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Tensiomètre BLE                                                 │
│  • Xiaomi Mi Smart Blood Pressure Monitor — ~25 €               │
│  • Omron M7 Intelli IT (BLE) — ~45 € (qualité médicale)         │
│  • AliExpress: "Smart Blood Pressure Monitor BLE" — ~12 €       │
│                                                                  │
│  Oxymètre BLE                                                    │
│  • Wellue O2Ring — ~25 € (port continu, idéal nouveau-né)       │
│  • Contec CMS50F — ~20 € (clip doigt)                            │
│  • Viatom Checkme O2 — ~30 €                                     │
│                                                                  │
│  Thermomètre BLE                                                 │
│  • Kinsa QuickCare — ~12 € (FDA approuvé, BLE)                  │
│  • Withings Thermo — ~70 € (haute précision, cher)              │
│  • Generic BLE Thermometer — ~8 € (AliExpress)                   │
│                                                                  │
│  Balance BLE                                                     │
│  • Xiaomi Mi Body Composition Scale 2 — ~18 €                   │
│  • Renpho Smart Scale — ~20 €                                    │
│  • Generic BLE Scale — ~12 € (AliExpress)                        │
│                                                                  │
│  Glucomètre BLE (optionnel)                                      │
│  • Accu-Chek Guide Me — ~50 €                                    │
│  • Contour Next One — ~30 €                                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 8. FEUILLE DE ROUTE TECHNIQUE

```
PHASE 1 — Support BLE de base (1 semaine)
├── Module ble_manager.js
├── Parsers IEEE 11073 pour tensiomètre + oxymètre + thermomètre
├── Boutons Scan dans l'interface
└── Mode dégradé (saisie manuelle)

PHASE 2 — Validation croisée (2 semaines)
├── Test avec 3 dispositifs physiques
├── Comparaison mesures BLE vs manuelles
├── Gestion des erreurs (timeout, batterie faible, déconnexion)
└── Documentation pour les agents de santé

PHASE 3 — Extension (1 mois)
├── Support glucomètre + balance
├── Mode « scan continu » pour monitoring (oxymètre néonatal)
├── Cache local des mesures (IndexedDB)
└── Export CSV pour registres de santé
```
