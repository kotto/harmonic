/**
 * KA Secure — QR visuel + Verrouillage PIN + Sauvegarde/Restauration
 * ==================================================================
 * Module partagé par KA Care et KA Patient.
 * 
 * 1. QR Code visuel (SVG, sans librairie externe)
 * 2. Verrouillage par PIN (4 chiffres)
 * 3. Sauvegarde/Restauration complète (JSON téléchargeable)
 */

const KA_SECURE = {
  
  // ═══════════════════════════════════════════════════
  // 1. QR CODE VISUEL (SVG)
  // ═══════════════════════════════════════════════════
  
  /**
   * Génère un QR code SVG dans un élément HTML.
   * Algorithme simplifié : matrice de points encodant le texte en binaire.
   * Pour un vrai QR code, utiliser une librairie comme qrcode.js.
   * Ici, on génère un DataMatrix-like visuel encodant les données.
   */
  generateQR(elementId, data) {
    const el = document.getElementById(elementId);
    if (!el) return;
    
    // Encoder les données en base64
    const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(data))));
    
    // Créer une matrice QR simplifiée (21x21 pour version standard)
    const size = 21;
    const matrix = this._buildQRMatrix(encoded, size);
    
    // Générer le SVG
    const cellSize = 8;
    const margin = 4;
    const svgSize = size * cellSize + 2 * margin;
    
    let svg = `<svg width="${svgSize}" height="${svgSize}" viewBox="0 0 ${svgSize} ${svgSize}" xmlns="http://www.w3.org/2000/svg">`;
    svg += `<rect width="${svgSize}" height="${svgSize}" fill="white"/>`;
    
    // Patterns de position (coins)
    this._drawFinderPattern(svg, margin, margin, cellSize);
    this._drawFinderPattern(svg, margin + (size - 7) * cellSize, margin, cellSize);
    this._drawFinderPattern(svg, margin, margin + (size - 7) * cellSize, cellSize);
    
    // Dessiner les modules
    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        // Skip finder patterns
        if ((x < 7 && y < 7) || (x > size - 8 && y < 7) || (x < 7 && y > size - 8)) continue;
        if (matrix[y] && matrix[y][x]) {
          svg += `<rect x="${margin + x * cellSize}" y="${margin + y * cellSize}" width="${cellSize}" height="${cellSize}" fill="black"/>`;
        }
      }
    }
    
    svg += '</svg>';
    el.innerHTML = svg;
  },
  
  _buildQRMatrix(data, size) {
    const matrix = Array(size).fill().map(() => Array(size).fill(false));
    let idx = 0;
    // Encodage simplifié en zigzag (pas un vrai QR, mais visuellement similaire)
    for (let y = 0; y < size && idx < data.length * 8; y++) {
      for (let x = (y % 2 === 0) ? 0 : size - 1; 
           (y % 2 === 0) ? x < size : x >= 0; 
           x += (y % 2 === 0) ? 1 : -1) {
        // Skip finder areas
        if ((x < 7 && y < 7) || (x > size - 8 && y < 7) || (x < 7 && y > size - 8)) continue;
        if (idx < data.length * 8) {
          const charIdx = Math.floor(idx / 8);
          const bitIdx = idx % 8;
          if (charIdx < data.length) {
            const bit = (data.charCodeAt(charIdx) >> bitIdx) & 1;
            matrix[y][x] = bit === 1;
          }
          idx++;
        }
      }
    }
    return matrix;
  },
  
  _drawFinderPattern(svg, x, y, cellSize) {
    const s = 7 * cellSize;
    svg += `<rect x="${x}" y="${y}" width="${s}" height="${s}" fill="black"/>`;
    svg += `<rect x="${x + cellSize}" y="${y + cellSize}" width="${s - 2*cellSize}" height="${s - 2*cellSize}" fill="white"/>`;
    svg += `<rect x="${x + 2*cellSize}" y="${y + 2*cellSize}" width="${s - 4*cellSize}" height="${s - 4*cellSize}" fill="black"/>`;
  },

  // ═══════════════════════════════════════════════════
  // 2. VERROUILLAGE PIN
  // ═══════════════════════════════════════════════════
  
  PIN_KEY: 'ka_secure_pin',
  PIN_ATTEMPTS_KEY: 'ka_secure_attempts',
  MAX_ATTEMPTS: 5,
  LOCKOUT_MINUTES: 15,
  
  /**
   * Configure le PIN (premier lancement).
   */
  setPIN(pin) {
    if (pin.length !== 4 || !/^\d{4}$/.test(pin)) return false;
    localStorage.setItem(this.PIN_KEY, btoa(pin)); // encodage simple
    localStorage.setItem(this.PIN_ATTEMPTS_KEY, '0');
    return true;
  },
  
  /**
   * Vérifie si un PIN est configuré.
   */
  hasPIN() {
    return !!localStorage.getItem(this.PIN_KEY);
  },
  
  /**
   * Vérifie le PIN saisi.
   */
  verifyPIN(pin) {
    const stored = localStorage.getItem(this.PIN_KEY);
    if (!stored) return true; // Pas de PIN configuré
    
    const attempts = parseInt(localStorage.getItem(this.PIN_ATTEMPTS_KEY) || '0');
    
    // Vérifier le verrouillage temporaire
    const lockoutUntil = localStorage.getItem('ka_secure_lockout');
    if (lockoutUntil && Date.now() < parseInt(lockoutUntil)) {
      const remaining = Math.ceil((parseInt(lockoutUntil) - Date.now()) / 60000);
      return { blocked: true, remaining };
    }
    
    if (attempts >= this.MAX_ATTEMPTS) {
      const lockoutTime = Date.now() + this.LOCKOUT_MINUTES * 60000;
      localStorage.setItem('ka_secure_lockout', lockoutTime.toString());
      return { blocked: true, remaining: this.LOCKOUT_MINUTES };
    }
    
    const valid = atob(stored) === pin;
    if (!valid) {
      localStorage.setItem(this.PIN_ATTEMPTS_KEY, (attempts + 1).toString());
      return { valid: false, remaining: this.MAX_ATTEMPTS - attempts - 1 };
    }
    
    // PIN correct — reset
    localStorage.setItem(this.PIN_ATTEMPTS_KEY, '0');
    localStorage.removeItem('ka_secure_lockout');
    return { valid: true };
  },
  
  /**
   * Change le PIN.
   */
  changePIN(oldPin, newPin) {
    const result = this.verifyPIN(oldPin);
    if (!result.valid) return false;
    return this.setPIN(newPin);
  },
  
  /**
   * Supprime le PIN.
   */
  removePIN(pin) {
    const result = this.verifyPIN(pin);
    if (!result.valid) return false;
    localStorage.removeItem(this.PIN_KEY);
    localStorage.removeItem(this.PIN_ATTEMPTS_KEY);
    return true;
  },
  
  /**
   * Affiche l'écran de verrouillage PIN.
   * Appeler au chargement de l'application.
   */
  showLockScreen(onSuccess) {
    if (!this.hasPIN()) { onSuccess(); return; }
    
    // Créer l'overlay
    const overlay = document.createElement('div');
    overlay.id = 'kaLockScreen';
    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:#0d0d0d;z-index:9999;display:flex;align-items:center;justify-content:center;flex-direction:column';
    
    overlay.innerHTML = `
      <img src="logo2.jpg" style="width:60px;height:60px;border-radius:50%;object-fit:cover;margin-bottom:20px;box-shadow:0 4px 16px rgba(212,168,83,0.3)">
      <h2 style="color:#d4a853;font-size:1.2em;margin-bottom:4px">KA Secure</h2>
      <p style="color:#9b8f7e;font-size:.85em;margin-bottom:20px">Entrez votre code PIN</p>
      <div id="pinDots" style="display:flex;gap:12px;margin-bottom:16px">
        <div class="pin-dot" style="width:14px;height:14px;border-radius:50%;border:2px solid #4e4637"></div>
        <div class="pin-dot" style="width:14px;height:14px;border-radius:50%;border:2px solid #4e4637"></div>
        <div class="pin-dot" style="width:14px;height:14px;border-radius:50%;border:2px solid #4e4637"></div>
        <div class="pin-dot" style="width:14px;height:14px;border-radius:50%;border:2px solid #4e4637"></div>
      </div>
      <div id="pinError" style="color:#e74c3c;font-size:.75em;margin-bottom:8px;min-height:18px"></div>
      <div style="display:grid;grid-template-columns:repeat(3,60px);gap:8px">
        ${[1,2,3,4,5,6,7,8,9,'',0,'⌫'].map(k => 
          k === '' ? '<div></div>' :
          `<button onclick="KA_SECURE._pinInput('${k}')" style="width:60px;height:50px;border-radius:12px;border:1px solid #2a2a2a;background:#1a1a1a;color:#eae1d7;font-size:1.2em;cursor:pointer;font-family:inherit">${k}</button>`
        ).join('')}
      </div>
    `;
    
    document.body.appendChild(overlay);
    
    this._pinBuffer = '';
    this._pinCallback = onSuccess;
  },
  
  _pinBuffer: '',
  _pinCallback: null,
  
  _pinInput(key) {
    if (key === '⌫') {
      this._pinBuffer = this._pinBuffer.slice(0, -1);
    } else {
      if (this._pinBuffer.length < 4) this._pinBuffer += key;
    }
    
    // Mettre à jour les dots
    const dots = document.querySelectorAll('.pin-dot');
    dots.forEach((d, i) => {
      d.style.background = i < this._pinBuffer.length ? '#d4a853' : 'transparent';
      d.style.borderColor = i < this._pinBuffer.length ? '#d4a853' : '#4e4637';
    });
    
    // Vérifier si 4 chiffres
    if (this._pinBuffer.length === 4) {
      const result = this.verifyPIN(this._pinBuffer);
      const errEl = document.getElementById('pinError');
      
      if (result.blocked) {
        errEl.textContent = `Trop de tentatives. Réessayez dans ${result.remaining} min.`;
        this._pinBuffer = '';
      } else if (result.valid) {
        document.getElementById('kaLockScreen').remove();
        if (this._pinCallback) this._pinCallback();
      } else {
        errEl.textContent = `PIN incorrect. ${result.remaining} tentative(s) restante(s).`;
        this._pinBuffer = '';
        // Reset dots
        document.querySelectorAll('.pin-dot').forEach(d => {
          d.style.background = 'transparent';
          d.style.borderColor = '#4e4637';
        });
      }
    }
  },

  // ═══════════════════════════════════════════════════
  // 3. SAUVEGARDE / RESTAURATION
  // ═══════════════════════════════════════════════════
  
  /**
   * Exporte toutes les données de l'application en fichier JSON.
   * @param {string} appName - 'ka_care' ou 'ka_patient'
   */
  exportAll(appName) {
    const keys = appName === 'ka_care' 
      ? ['ka_care_patients', 'ka_care_history']
      : ['ka_patient_data'];
    
    const backup = {
      version: '1.0',
      app: appName,
      timestamp: new Date().toISOString(),
      data: {}
    };
    
    keys.forEach(k => {
      const val = localStorage.getItem(k);
      if (val) {
        try { backup.data[k] = JSON.parse(val); } 
        catch(e) { backup.data[k] = val; }
      }
    });
    
    // Télécharger
    const blob = new Blob([JSON.stringify(backup, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${appName}_backup_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    return true;
  },
  
  /**
   * Importe des données depuis un fichier JSON.
   * @param {File} file - Le fichier JSON sélectionné
   * @param {string} appName - 'ka_care' ou 'ka_patient'
   * @param {function} onSuccess - Callback après import réussi
   */
  importAll(file, appName, onSuccess) {
    const reader = new FileReader();
    reader.onload = function(e) {
      try {
        const backup = JSON.parse(e.target.result);
        
        if (backup.app !== appName) {
          alert(`Ce fichier appartient à ${backup.app}, pas à ${appName}.`);
          return;
        }
        
        // Restaurer les données
        Object.entries(backup.data).forEach(([key, value]) => {
          localStorage.setItem(key, JSON.stringify(value));
        });
        
        alert(`✅ Sauvegarde restaurée !\n${Object.keys(backup.data).length} clés importées.\nDate: ${backup.timestamp}\n\nRechargez l'application.`);
        if (onSuccess) onSuccess();
      } catch(err) {
        alert('❌ Fichier invalide ou corrompu.');
      }
    };
    reader.readAsText(file);
  },
  
  /**
   * Crée un bouton de sélection de fichier pour l'import.
   */
  triggerImport(appName, onSuccess) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = function(e) {
      if (e.target.files[0]) {
        KA_SECURE.importAll(e.target.files[0], appName, onSuccess);
      }
    };
    input.click();
  }
};
