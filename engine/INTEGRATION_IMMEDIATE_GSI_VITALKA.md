# 🚀 INTÉGRATION IMMÉDIATE DU GSI DANS VITAL KA

## Plan d'extension du module BLE et des constantes vitales pour la Médecine Harmonique

---

> **Constat :** VITAL KA dispose déjà d'un module BLE (Bluetooth Low Energy) dans l'application médecin, d'un module « Constantes Vitales » dans l'application patient, et d'une architecture offline. Le GSI peut être intégré immédiatement en étendant ces modules existants, sans refonte de l'application.

---

## I. CE QUI EXISTE DÉJÀ

### 1.1 Dans VITAL KA

| Module | Fichier | Fonction actuelle | Potentiel GSI |
|--------|---------|-------------------|---------------|
| **BLE** | `vital_ka_ble.js` | Stub (vide) | ⬅️ **À remplacer par le module complet** |
| **Constantes vitales** | `ka_patient.html` (screen-vitals) | Saisie manuelle (poids, tension, glycémie…) | ⬅️ **À enrichir des mesures BLE + GSI** |
| **Profil médecin** | `ka_medecins.html` | Module BLE (tensiomètre, saturomètre, thermomètre) | ⬅️ **À étendre aux capteurs GSI** |
| **IA** | `vital_ka_ai.js` | IA déterministe (44 pathologies) | ⬅️ **À enrichir du module GSI** |
| **Stockage** | LocalStorage + sync Cloud | Dossier patient offline | ✅ Compatible |

### 1.2 Les capteurs BLE disponibles immédiatement

| Capteur | Mesure GSI | Prix | Disponibilité | Marques testées |
|---------|-----------|------|---------------|-----------------|
| **ECG 1 dérivation** (KardiaMobile) | S/D, LF/HF, FC | 89-120 € | Commercial | AliveCor, Wellue |
| **Thermomètre IR** (Braun, iHealth) | T° | 30-50 € | Commercial | Braun, iHealth, Withings |
| **Saturomètre BLE** (Wellue, iHealth) | FC, SatO2 | 30-60 € | Commercial | Wellue, iHealth, Nonin |
| **Tensiomètre BLE** (Omron, Withings) | PA, FC | 50-100 € | Commercial | Omron, Withings, iHealth |
| **EEG portable** (NeuroSky, Emotiv) | β/α | 100-400 € | Commercial | NeuroSky MindWave, Emotiv Insight |

---

## II. PLAN D'INTÉGRATION IMMÉDIATE — 3 PHASES

### Phase 1 — Module BLE complet (Semaine 1-2)

Remplacer le stub BLE par un module fonctionnel qui connecte les capteurs ECG, T°, SpO2, PA.

#### 1.1 Nouveau fichier `vital_ka_ble.js`

```javascript
// Vital Ka BLE — GSI Medical Device Hub
// Web Bluetooth API pour les capteurs de la Médecine Harmonique
// Version 1.0 — Consultations médicales + auto-mesure patient

const KA_BLE = {
  // État des connexions
  devices: { ecg: null, therm: null, spo2: null, bp: null, eeg: null },
  measurements: { sd: null, lfhf: null, ie: null, ba: null, temp: null },
  gsi: null,
  
  // Services BLE standard (UUIDs)
  SERVICES: {
    ecg: { service: '0000fff0-0000-1000-8000-00805f9b34fb', // UUID standard ECG
           char: '0000fff1-0000-1000-8000-00805f9b34fb' },
    therm: { service: '00001809-0000-1000-8000-00805f9b34fb', // Health Thermometer
             char: '00002a1c-0000-1000-8000-00805f9b34fb' },
    spo2: { service: '00001822-0000-1000-8000-00805f9b34fb', // Pulse Oximeter
            char: '00002a5e-0000-1000-8000-00805f9b34fb' },
    bp: { service: '00001810-0000-1000-8000-00805f9b34fb', // Blood Pressure
          char: '00002a35-0000-1000-8000-00805f9b34fb' },
    eeg: { service: '0000ffd0-0000-1000-8000-00805f9b34fb', // EEG (NeuroSky)
           char: '0000ffd1-0000-1000-8000-00805f9b34fb' }
  },

  // Initialisation
  init: function() {
    if (!navigator.bluetooth) {
      console.warn('Web Bluetooth non supporté sur ce navigateur.');
      return false;
    }
    return true;
  },

  // Scan des appareils disponibles
  scan: async function(type) {
    if (!this.init()) return;
    try {
      const device = await navigator.bluetooth.requestDevice({
        filters: [{ services: [this.SERVICES[type].service] }],
        optionalServices: Object.values(this.SERVICES).map(s => s.service)
      });
      this.devices[type] = device;
      await this.connect(type);
      return device;
    } catch (e) {
      console.error('BLE scan error:', e);
      return null;
    }
  },

  // Connexion à un appareil
  connect: async function(type) {
    if (!this.devices[type]) return;
    const server = await this.devices[type].gatt.connect();
    const service = await server.getPrimaryService(this.SERVICES[type].service);
    const char = await service.getCharacteristic(this.SERVICES[type].char);
    
    await char.startNotifications();
    char.addEventListener('characteristicvaluechanged', (e) => {
      this.handleData(type, e.target.value);
    });
  },

  // Traitement des données reçues
  handleData: function(type, data) {
    switch(type) {
      case 'ecg':
        const rr = this.parseECG(data); // Intervalles RR
        this.measurements.sd = this.calcSD(rr); // S/D ratio
        this.measurements.lfhf = this.calcLFHF(rr); // LF/HF
        break;
      case 'therm':
        this.measurements.temp = this.parseThermometer(data);
        break;
      case 'eeg':
        const bands = this.parseEEG(data);
        this.measurements.ba = bands.beta / bands.alpha; // β/α ratio
        break;
    }
    this.calcGSI();
    this.updateUI();
  },

  // Calcul du GSI
  calcGSI: function() {
    const phi = 1.6180339887;
    const invPhi = 1 / phi;
    const { sd, lfhf, ie, ba, temp } = this.measurements;
    
    let delta = [];
    if (sd) delta.push(Math.abs(sd - invPhi));
    if (lfhf) delta.push(Math.abs(lfhf - phi) / phi);
    if (ie) delta.push(Math.abs(ie - invPhi));
    if (ba) delta.push(Math.abs(ba - phi) / phi);
    if (temp) delta.push(Math.abs(temp - 37.0) / 37.0);
    
    this.gsi = delta.length > 0 
      ? delta.reduce((a, b) => a + b, 0) / delta.length 
      : null;
    
    return this.gsi;
  },

  // Interprétation du GSI
  interpret: function(gsi) {
    if (gsi === null) return { color: '#666', text: 'En attente…' };
    if (gsi < 0.03) return { color: '#27ae60', text: 'Santé optimale ✅' };
    if (gsi < 0.06) return { color: '#f39c12', text: 'Santé moyenne 🟡' };
    if (gsi < 0.10) return { color: '#e67e22', text: 'Risque modéré 🟠' };
    return { color: '#e74c3c', text: 'Risque élevé 🔴' };
  },

  // Mise à jour de l'interface
  updateUI: function() {
    const event = new CustomEvent('gsi-update', { 
      detail: { 
        measurements: this.measurements, 
        gsi: this.gsi,
        interpretation: this.interpret(this.gsi)
      }
    });
    document.dispatchEvent(event);
  },

  // Déconnexion
  disconnect: function(type) {
    if (this.devices[type]?.gatt?.connected) {
      this.devices[type].gatt.disconnect();
    }
    this.devices[type] = null;
    this.measurements[type === 'ecg' ? 'sd' : 
                      type === 'therm' ? 'temp' : 
                      type === 'eeg' ? 'ba' : null] = null;
    this.calcGSI();
    this.updateUI();
  },

  // --- Parsers spécifiques (à compléter par marque) ---
  parseECG: function(data) { /* RR intervals from KardiaMobile, Wellue… */ },
  parseThermometer: function(data) { /* iHealth, Braun… */ },
  parseEEG: function(data) { /* NeuroSky, Emotiv… */ },
  calcSD: function(rr) { /* Systole/Diastole from ECG */ },
  calcLFHF: function(rr) { /* LF/HF from HRV analysis (Welch) */ },
};
```

#### 1.2 Intégration dans l'application médecin

Ajouter dans `ka_medecins.html` (section BLE existante, ligne 349) :

```html
<!-- GSI MODULE — extended from existing BLE card -->
<div class="card" id="gsiCard">
  <h3>🌿 GSI — Golden Health Index</h3>
  
  <!-- Capteurs BLE -->
  <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px">
    <button class="btn btn-secondary" style="width:auto;padding:8px 14px;font-size:11px" onclick="connectBLE('ecg')">
      📡 ECG
    </button>
    <button class="btn btn-secondary" style="width:auto;padding:8px 14px;font-size:11px" onclick="connectBLE('therm')">
      🌡️ T°
    </button>
    <button class="btn btn-secondary" style="width:auto;padding:8px 14px;font-size:11px" onclick="connectBLE('spo2')">
      🫁 SpO2
    </button>
    <button class="btn btn-secondary" style="width:auto;padding:8px 14px;font-size:11px" onclick="connectBLE('eeg')">
      🧠 EEG
    </button>
  </div>

  <!-- Résultats GSI -->
  <div id="gsiLive" style="text-align:center;padding:16px;background:rgba(15,15,25,.8);border-radius:12px;margin-bottom:8px">
    <div id="gsiValue" style="font-size:2.4em;font-weight:800;color:#666">--</div>
    <div id="gsiText" style="font-size:.8em;color:var(--muted);margin-top:4px">Connectez un capteur</div>
  </div>

  <!-- Radar des 5 oscillateurs -->
  <canvas id="gsiRadar" width="200" height="200" style="width:100%;max-width:200px;margin:8px auto;display:block"></canvas>
  
  <!-- Détail des mesures -->
  <div id="gsiDetails" style="font-size:12px;color:var(--muted)"></div>
</div>
```

### Phase 2 — Module Constantes Vitales enrichi (Semaine 2-3)

Étendre le module « Constantes vitales » de l'application patient pour afficher le GSI.

#### 2.1 Ajout dans `ka_patient.html` (screen-vitals, ligne 210)

```html
<div class="screen" id="screen-vitals">
  <h2 style="margin-bottom:16px">📊 Constantes et GSI</h2>
  
  <!-- GSI Card -->
  <div class="card" id="gsiCard">
    <h3>🌿 GSI — Indice de Santé d'Or</h3>
    <div id="gsiPatientDisplay" style="text-align:center;padding:12px">
      <div id="gsiValuePatient" style="font-size:2em;font-weight:800;color:#666">--</div>
      <div style="font-size:12px;color:var(--muted);margin-top:4px">
        Golden Health Index — mesuré par le médecin
      </div>
    </div>
  </div>

  <!-- 5 oscillateurs -->
  <div class="card">
    <h3>📈 Mes 5 oscillateurs</h3>
    <div id="oscillatorList">
      <div class="vital-row"><span class="vital-label">❤️ Cœur (S/D)</span><span class="vital-value" id="oscSD">--</span></div>
      <div class="vital-row"><span class="vital-label">💓 Variabilité (LF/HF)</span><span class="vital-value" id="oscLFHF">--</span></div>
      <div class="vital-row"><span class="vital-label">🫁 Respiration (I/E)</span><span class="vital-value" id="oscIE">--</span></div>
      <div class="vital-row"><span class="vital-label">🧠 Cerveau (β/α)</span><span class="vital-value" id="oscBA">--</span></div>
      <div class="vital-row"><span class="vital-label">🌡️ Température</span><span class="vital-value" id="oscTemp">--</span></div>
    </div>
  </div>

  <!-- Mesures existantes -->
  <div class="card">
    <h3>➕ Ajouter une mesure</h3>
    <div class="row">
      <input id="vitalType" placeholder="Type (poids, tension, glycémie…)">
      <input id="vitalValue" placeholder="Valeur">
    </div>
    <input id="vitalUnit" placeholder="Unité (kg, mmHg, g/L...)" style="margin-top:8px">
    <button class="btn btn-primary" style="margin-top:8px;padding:12px" onclick="addVital()">✅ Enregistrer</button>
  </div>
  
  <div id="vitalList"><div class="card"><p style="text-align:center;color:var(--muted)">Aucune mesure enregistrée.</p></div></div>
</div>
```

### Phase 3 — Synchronisation GSI Patient ↔ Médecin (Semaine 3-4)

Le GSI mesuré par le médecin est synchronisé dans le dossier patient via le QR code existant.

```
Flux de synchronisation :
  1. Médecin connecte les capteurs BLE → GSI calculé
  2. GSI + 5 oscillateurs sont stockés dans le dossier patient (local)
  3. QR code patient scanné par le médecin → GSI partagé
  4. Patient voit son GSI en temps réel
  5. Historique GSI conservé (courbe d'évolution)
```

---

## III. CAPTEURS PRIORITAIRES — GUIDE D'ACHAT

### 3.1 ECG — KardiaMobile (AliveCor) — 89 €

```
• Marque : AliveCor KardiaMobile (1 dérivation)
• Prix : 89-120 € (selon revendeur)
• Bluetooth : BLE 4.0
• Application : Kardia App (iOS/Android)
• Données GSI : S/D, LF/HF, FC
• Acquisition : 30 secondes à 5 minutes
• Disponibilité : Amazon, pharmacies, AliveCor store
• Référence : RM-0100 (KardiaMobile 1L)
```

### 3.2 Thermomètre — iHealth PT03BLE — 30 €

```
• Marque : iHealth PT03BLE
• Prix : 30 €
• Bluetooth : BLE 4.0
• Type : Infrarouge frontal
• Données GSI : T° (0,1 °C de précision)
• Acquisition : 1 seconde
• Disponibilité : Amazon, iHealth store
```

### 3.3 Saturomètre — Wellue O2Ring — 60 €

```
• Marque : Wellue O2Ring
• Prix : 60 €
• Bluetooth : BLE 4.0
• Type : Oxymètre de pouls (doigt)
• Données GSI : FC, SpO2
• Acquisition : continue
• Disponibilité : Amazon, Wellue store
```

### 3.4 EEG — NeuroSky MindWave Mobile 2 — 100 €

```
• Marque : NeuroSky MindWave Mobile 2
• Prix : 100 €
• Bluetooth : BLE 4.0
• Données GSI : β/α (attention, méditation)
• Acquisition : 1 minute
• Disponibilité : NeuroSky, Amazon
• Note : EEG à 1 canal, mesure β/α approximative
```

---

## IV. CODE D'INTÉGRATION — FICHIERS À MODIFIER

### 4.1 Liste des fichiers

| Fichier | Action | Priorité |
|---------|--------|----------|
| `vital_ka_ble.js` | Remplacer par le module BLE GSI complet (ci-dessus) | 🔴 Immédiate |
| `vital-ka/apps/medecins/ka_medecins.html` | Ajouter la carte GSI + connecteurs BLE | 🔴 Immédiate |
| `vital-ka/apps/patient/ka_patient.html` | Ajouter l'affichage GSI + 5 oscillateurs | 🔴 Immédiate |
| `vital_ka_ai.js` | Ajouter le module de calcul GSI + arbre de décision | 🟡 Phase 2 |
| `vital_ka_config.js` | Ajouter les constantes (φ, seuils GSI) | 🟡 Phase 2 |

### 4.2 Ordre d'intégration

```
1. vital_ka_ble.js → module BLE complet (connecter ECG, T°, EEG)
2. ka_medecins.html → interface de mesure GSI (médecin)
3. ka_patient.html → affichage GSI (patient)
4. vital_ka_ai.js → arbre de décision GSI + 44 pathologies enrichies
```

---

## V. DÉMONSTRATION RAPIDE — 15 MINUTES CHRONO

```
1. Ouvrir ka_medecins.html sur smartphone médecin
2. Cliquer « 📡 ECG » → connecter KardiaMobile (BLE)
3. Poser ECG sur les doigts du patient → 30 secondes
4. GSI apparaît en temps réel
5. Cliquer « 🌡️ T° » → connecter iHealth → 1 seconde
6. GSI mis à jour avec T°
7. Radar des 5 oscillateurs visible
8. Résultat : vert/jaune/rouge
9. QR code patient → données partagées dans le dossier
10. Patient voit son GSI sur son app
```

**Temps total : 15 minutes, 2 capteurs BLE, 1 application déjà existante.**

---

## VI. BUDGET DE L'INTÉGRATION IMMÉDIATE

| Poste | Coût | Délai |
|-------|------|-------|
| Développement module BLE (vital_ka_ble.js) | 5 000 € | 1 semaine |
| Intégration application médecin (ka_medecins.html) | 3 000 € | 1 semaine |
| Intégration application patient (ka_patient.html) | 2 000 € | 1 semaine |
| Tests capteurs BLE (3 marques) | 1 000 € | 1 semaine |
| **Total** | **11 000 €** | **4 semaines** |

---

> *« L'intégration immédiate du GSI dans VITAL KA ne nécessite pas de refonte — elle étend ce qui existe déjà. Le module BLE passe d'un stub à un hub de capteurs harmoniques. Les constantes vitales deviennent des oscillateurs d'or. Le QR code devient le synchroniseur patient-médecin. 11 000 € et 4 semaines pour que VITAL KA devienne la première plateforme de santé africaine avec diagnostic harmonique intégré. »*
>
> — **Kotto Alain**, 12/08/2026