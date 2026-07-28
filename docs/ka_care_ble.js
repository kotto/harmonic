/**
 * KA Care — Module Objets Médicaux Connectés (BLE)
 * =================================================
 * Connecte des dispositifs Bluetooth Low Energy (tensiomètre,
 * oxymètre, thermomètre, glucomètre, ECG) directement depuis
 * le navigateur (Chrome/Edge Android & Desktop).
 * 
 * Inclusion : <script src="ka_care_ble.js"></script>
 * Usage :     ble.startScan(); // lance le scan des dispositifs
 */

const KA_BLE = {
  devices: [],
  connected: null,
  server: null,
  vitals: { heartRate: '--', spo2: '--', temperature: '--', bloodPressure: '--/--', glucose: '--' },
  
  // UUIDs standards BLE pour dispositifs médicaux
  SERVICES: {
    heartRate:    0x180D,  // Heart Rate
    bloodPressure:0x1810,  // Blood Pressure
    healthThermo: 0x1809,  // Health Thermometer
    pulseOximeter:0x1822,  // Pulse Oximeter (continu)
    glucose:      0x1808,  // Glucose
    deviceInfo:   0x180A,  // Device Information
    battery:      0x180F,  // Battery Service
  },
  
  // Vérifier si le navigateur supporte Web Bluetooth
  isSupported() {
    return 'bluetooth' in navigator;
  },
  
  // Scanner les dispositifs BLE médicaux à proximité
  async startScan() {
    if (!this.isSupported()) {
      alert('Web Bluetooth non supporté sur ce navigateur. Utilisez Chrome ou Edge sur Android/Desktop.');
      return;
    }
    
    try {
      const device = await navigator.bluetooth.requestDevice({
        acceptAllDevices: true,
        optionalServices: Object.values(this.SERVICES).map(s => s.toString(16).padStart(4, '0'))
      });
      
      await this.connect(device);
    } catch (err) {
      if (err.name !== 'NotFoundError') {
        console.error('BLE scan error:', err);
      }
    }
  },
  
  // Se connecter à un dispositif
  async connect(device) {
    try {
      this.server = await device.gatt.connect();
      this.connected = device;
      
      // Détecter quel type de dispositif
      const services = await this.server.getPrimaryServices();
      
      for (const service of services) {
        const uuid = parseInt(service.uuid.replace('0000', '').replace('-0000-1000-8000-00805f9b34fb', ''), 16);
        
        if (uuid === this.SERVICES.heartRate) {
          await this._startHeartRate(service);
        } else if (uuid === this.SERVICES.bloodPressure) {
          await this._startBloodPressure(service);
        } else if (uuid === this.SERVICES.healthThermo) {
          await this._startThermometer(service);
        } else if (uuid === this.SERVICES.pulseOximeter) {
          await this._startPulseOximeter(service);
        } else if (uuid === this.SERVICES.glucose) {
          await this._startGlucose(service);
        }
      }
      
      this._updateUI();
      this._onStatusChange('connected', device.name || 'Dispositif connecté');
    } catch (err) {
      console.error('BLE connect error:', err);
      this._onStatusChange('error', err.message);
    }
  },
  
  // ── Heart Rate Monitor ──────────────────────────────
  async _startHeartRate(service) {
    const characteristic = await service.getCharacteristic(0x2A37); // Heart Rate Measurement
    await characteristic.startNotifications();
    characteristic.addEventListener('characteristicvaluechanged', (event) => {
      const value = event.target.value;
      const flags = value.getUint8(0);
      const hr = value.getUint8(1); // 8-bit HR value
      this.vitals.heartRate = hr;
      this._updateUI();
      this._onVitalUpdate('heartRate', hr);
    });
  },
  
  // ── Blood Pressure Monitor ──────────────────────────
  async _startBloodPressure(service) {
    const characteristic = await service.getCharacteristic(0x2A35); // Blood Pressure Measurement
    await characteristic.startNotifications();
    characteristic.addEventListener('characteristicvaluechanged', (event) => {
      const value = event.target.value;
      const flags = value.getUint8(0);
      const systolic = value.getUint16(1, true);  // mmHg
      const diastolic = value.getUint16(3, true); // mmHg
      this.vitals.bloodPressure = systolic + '/' + diastolic;
      this._updateUI();
      this._onVitalUpdate('bloodPressure', systolic + '/' + diastolic);
    });
  },
  
  // ── Thermometer ─────────────────────────────────────
  async _startThermometer(service) {
    const characteristic = await service.getCharacteristic(0x2A1C); // Temperature Measurement
    await characteristic.startNotifications();
    characteristic.addEventListener('characteristicvaluechanged', (event) => {
      const value = event.target.value;
      const temp = value.getUint32(0, true) / 1000.0; // Convertir en °C (IEEE 11073)
      this.vitals.temperature = temp.toFixed(1);
      this._updateUI();
      this._onVitalUpdate('temperature', temp.toFixed(1));
    });
  },
  
  // ── Pulse Oximeter ──────────────────────────────────
  async _startPulseOximeter(service) {
    const characteristic = await service.getCharacteristic(0x2A5F); // PLX Continuous Measurement
    await characteristic.startNotifications();
    characteristic.addEventListener('characteristicvaluechanged', (event) => {
      const value = event.target.value;
      const flags = value.getUint8(0);
      const spo2 = value.getUint16(1, true) / 100.0; // %
      this.vitals.spo2 = spo2.toFixed(0);
      this._updateUI();
      this._onVitalUpdate('spo2', spo2.toFixed(0));
    });
  },
  
  // ── Glucose ─────────────────────────────────────────
  async _startGlucose(service) {
    const characteristic = await service.getCharacteristic(0x2A18); // Glucose Measurement
    await characteristic.startNotifications();
    characteristic.addEventListener('characteristicvaluechanged', (event) => {
      const value = event.target.value;
      const flags = value.getUint8(0);
      const glucose = value.getUint16(5, true); // mg/dL
      this.vitals.glucose = glucose;
      this._updateUI();
      this._onVitalUpdate('glucose', glucose);
    });
  },
  
  // ── UI ──────────────────────────────────────────────
  _updateUI() {
    const el = document.getElementById('bleVitals');
    if (!el) return;
    el.innerHTML = `
      <div class="vital-grid">
        <div class="vital-card"><div class="value" style="color:${this.vitals.heartRate!=='--'?'var(--primary)':'var(--outline)'}">${this.vitals.heartRate}</div><div class="label">BPM — Cardiaque</div></div>
        <div class="vital-card"><div class="value" style="color:${this.vitals.bloodPressure!=='--/--'?'var(--primary)':'var(--outline)'}">${this.vitals.bloodPressure}</div><div class="label">mmHg — Tension</div></div>
        <div class="vital-card"><div class="value" style="color:${this.vitals.spo2!=='--'?'var(--primary)':'var(--outline)'}">${this.vitals.spo2}%</div><div class="label">SpO2 — Oxygène</div></div>
        <div class="vital-card"><div class="value" style="color:${this.vitals.temperature!=='--'?'var(--primary)':'var(--outline)'}">${this.vitals.temperature}°C</div><div class="label">Température</div></div>
      </div>
      ${this.vitals.glucose !== '--' ? `<div class="vital-card" style="margin-top:8px"><div class="value" style="color:var(--primary)">${this.vitals.glucose}</div><div class="label">mg/dL — Glycémie</div></div>` : ''}
    `;
  },
  
  _onStatusChange(status, message) {
    const el = document.getElementById('bleStatus');
    if (!el) return;
    const colors = { connected: 'var(--success)', error: 'var(--error)', scanning: 'var(--primary)' };
    el.innerHTML = `<span style="color:${colors[status]||'var(--outline)'};font-size:11px;letter-spacing:.05em">${status === 'connected' ? '🟢 ' + message : status === 'scanning' ? '🔵 Scan...' : '🔴 ' + message}</span>`;
  },
  
  _onVitalUpdate(type, value) {
    // Callback pour intégration avec le diagnostic harmonique
    // Le ψ du patient peut être mis à jour en temps réel avec les constantes
    console.log(`Vital update: ${type} = ${value}`);
  },
  
  disconnect() {
    if (this.server) { this.server.disconnect(); this.connected = null; }
    this.vitals = { heartRate: '--', spo2: '--', temperature: '--', bloodPressure: '--/--', glucose: '--' };
    this._updateUI();
    this._onStatusChange('error', 'Déconnecté');
  }
};

// Auto-init : vérifier si le navigateur supporte Web Bluetooth
if (!KA_BLE.isSupported()) {
  console.log('Web Bluetooth non supporté — constantes simulées');
}
