/**
 * KA Network — Gestion réseau WiFi & local
 * ==========================================
 * Détecte l'état du réseau, l'IP locale, et optimise
 * la connexion P2P pour la télémédecine hors-Internet.
 * 
 * Usage :
 *   KA_Network.getStatus() → { online, type, localIP, quality }
 *   KA_Network.onChange(callback)
 */

const KA_Network = {
  _localIP: null,
  _online: navigator.onLine,
  _type: 'unknown',
  _quality: 'unknown',
  _listeners: [],
  
  /**
   * Initialise la détection réseau
   */
  async init() {
    // Écouter les changements de connectivité
    window.addEventListener('online', () => this._updateStatus(true));
    window.addEventListener('offline', () => this._updateStatus(false));
    
    // Détecter le type de connexion si disponible
    if (navigator.connection) {
      this._type = navigator.connection.effectiveType || 'unknown';
      navigator.connection.addEventListener('change', () => {
        this._type = navigator.connection.effectiveType || 'unknown';
        this._notify();
      });
    }
    
    // Obtenir l'IP locale via WebRTC
    await this._detectLocalIP();
    
    // Mesurer la qualité réseau
    this._measureQuality();
    
    return this.getStatus();
  },
  
  /**
   * Retourne le statut réseau actuel
   */
  getStatus() {
    return {
      online: this._online,
      type: this._type,
      localIP: this._localIP,
      quality: this._quality,
      isWiFi: this._type === '4g' ? false : this._online,
      canP2P: !!this._localIP
    };
  },
  
  /**
   * Enregistre un callback appelé quand le statut change
   */
  onChange(cb) {
    this._listeners.push(cb);
  },
  
  /**
   * Vérifie si deux IP sont sur le même sous-réseau
   */
  sameSubnet(ip1, ip2) {
    if (!ip1 || !ip2) return false;
    const p1 = ip1.split('.').slice(0, 3).join('.');
    const p2 = ip2.split('.').slice(0, 3).join('.');
    return p1 === p2;
  },
  
  /**
   * Crée une configuration ICE optimisée pour le réseau local
   */
  getIceConfig() {
    const config = {
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
      ]
    };
    
    // Si IP locale détectée, ajouter des candidats hôtes
    if (this._localIP) {
      // Les candidats hôtes sont automatiquement inclus par le navigateur
      // On peut ajouter un serveur STUN local si disponible
    }
    
    return config;
  },
  
  // ═══ INTERNE ═══
  
  _updateStatus(online) {
    this._online = online;
    if (!online) {
      this._quality = 'offline';
    } else {
      this._measureQuality();
    }
    this._notify();
  },
  
  _notify() {
    const status = this.getStatus();
    this._listeners.forEach(cb => cb(status));
  },
  
  /**
   * Détecte l'IP locale via WebRTC (candidats ICE hôtes)
   */
  async _detectLocalIP() {
    return new Promise((resolve) => {
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
      });
      
      const timeout = setTimeout(() => {
        pc.close();
        resolve();
      }, 3000);
      
      pc.createDataChannel('ip-detect');
      pc.createOffer().then(offer => pc.setLocalDescription(offer));
      
      pc.onicecandidate = (event) => {
        if (!event.candidate) {
          clearTimeout(timeout);
          pc.close();
          resolve();
          return;
        }
        
        const candidate = event.candidate.candidate;
        // Extraire l'IP du candidat (format: "candidate:... typ host ...")
        const ipMatch = candidate.match(/(\d+\.\d+\.\d+\.\d+)/);
        if (ipMatch && candidate.includes('typ host')) {
          const ip = ipMatch[1];
          // Ignorer les IPs de loopback/virtuelles évidentes
          if (!ip.startsWith('127.') && !ip.startsWith('0.') && ip !== '0.0.0.0') {
            this._localIP = ip;
            this._notify();
          }
        }
      };
      
      // Fallback si pas de candidat
      setTimeout(() => {
        if (!this._localIP) {
          pc.close();
          resolve();
        }
      }, 2000);
    });
  },
  
  /**
   * Mesure la qualité réseau (latence estimée)
   */
  async _measureQuality() {
    if (!this._online) {
      this._quality = 'offline';
      return;
    }
    
    const start = performance.now();
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 3000);
      
      await fetch('https://www.google.com/favicon.ico', {
        mode: 'no-cors',
        signal: controller.signal
      });
      
      clearTimeout(timeout);
      const latency = performance.now() - start;
      
      if (latency < 150) this._quality = 'excellent';
      else if (latency < 400) this._quality = 'good';
      else if (latency < 1000) this._quality = 'slow';
      else this._quality = 'poor';
      
    } catch (e) {
      if (this._localIP) {
        this._quality = 'local-only';
      } else {
        this._quality = 'offline';
      }
    }
    
    this._notify();
  },
  
  /**
   * Détecte si le serveur KA local est actif sur le port 8765
   * @returns {Promise<string|null>} URL du serveur ou null
   */
  async detectKAServer() {
    if (!this._localIP) return null;
    const url = `http://${this._localIP}:8765/ka_patient.html`;
    try {
      const controller = new AbortController();
      setTimeout(() => controller.abort(), 1500);
      const resp = await fetch(url, { method: 'HEAD', signal: controller.signal });
      return resp.ok ? url : null;
    } catch {
      return null;
    }
  }
};

// Export global
if (typeof window !== 'undefined') {
  window.KA_Network = KA_Network;
}
