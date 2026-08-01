/* ══════════════════════════════════════════════════════════════════════════
   VITAL KA — Configuration Centralisée
   ══════════════════════════════════════════════════════════════════════════
   Source unique de vérité pour les paramètres applicatifs.
   Chargée EN PREMIER par vital_ka.html et ka_patient.html.

   Pour changer un port ou une voix : modifier ici, recharger l'app.
   ══════════════════════════════════════════════════════════════════════════ */
'use strict';

const VITAL_KA_CONFIG = {

  // ── Version applicative (affichée sur le splash + service worker) ──
  version: '2.1.0',

  // ── Ports des serveurs locaux ──
  ports: {
    app:   8765,   // ka_serve.py        — application web
    voice: 8420,   // ka_voice_server.py — synthèse Piper TTS
    phone: 8421,   // ka_phone (optionnel) — IA conversationnelle avancée
  },

  // ── Plateforme (détection WebView native Android / Capacitor) ──
  // En natif : pas de serveurs Python → TTS système + STT plugin (vital_ka_native.js)
  platform: {
    get isNative() {
      try {
        return !!(window.Capacitor && typeof window.Capacitor.isNativePlatform === 'function'
                  && window.Capacitor.isNativePlatform());
      } catch (e) { return false; }
    },
  },

  // ── Voix (Piper neuronal, offline) ──
  voice: {
    // Voix active (modifiable via le sélecteur dans Harmonic AI)
    // Persiste dans localStorage sous 'vital_ka_voice'
    get active() {
      try { return localStorage.getItem('vital_ka_voice') || this.name; }
      catch(e) { return this.name; }
    },
    set active(v) {
      try { localStorage.setItem('vital_ka_voice', v); } catch(e) {}
    },
    name: 'fr_FR-siwis-medium',   // voix par défaut

    // Mode natif Android : pas de serveur Piper → voix système (Web Speech)
    get nativeMode() { return VITAL_KA_CONFIG.platform.isNative; },

    // Catalogue complet des voix françaises disponibles
    availableVoices: [
      { id: 'fr_FR-siwis-medium', label: 'Siwis (F) — claire, naturelle',    gender: 'F', quality: 'medium', size: 62 },
      { id: 'fr_FR-upmc-medium',  label: 'UPMC (N) — académique, posée',     gender: 'N', quality: 'medium', size: 75 },
      { id: 'fr_FR-tom-medium',   label: 'Tom (M) — professionnelle',        gender: 'M', quality: 'medium', size: 62 },
      { id: 'fr_FR-gilles-low',   label: 'Gilles (M) — volume élevé',        gender: 'M', quality: 'low',    size: 62 },
      { id: 'fr_FR-siwis-low',    label: 'Siwis Light (F) — rapide, léger',  gender: 'F', quality: 'low',    size: 27 },
      { id: 'fr_FR-mls-medium',   label: 'MLS (M/N) — 124 locuteurs',        gender: 'N', quality: 'medium', size: 75 },
    ],

    // speed → length_scale via serveur : h_speed = clamp(1.50 − speed×1.08)
    //   0.82 → length_scale ≈ 1.0 (débit naturel)
    //   0.70 → length_scale ≈ 1.3 (plus lent, posé)
    profiles: {
      conseiller: { speed: 0.82, rate: 1.0,  pitch: 1.0  },
      compagnon:  { speed: 0.70, rate: 0.88, pitch: 1.05 },
    },
    // Timeouts réseau (ms)
    healthTimeoutMs: 2500,
    synthTimeoutMs:  15000,
  },

  // ── Reconnaissance vocale (Web Speech API) ──
  stt: {
    lang: 'fr-FR',
    silenceMs: 1800,        // silence avant envoi auto (conversation naturelle)
    maxListenMs: 30000,     // sécurité push-to-talk
  },

  // ── Endpoints dérivés (calculés au chargement) ──
  get voiceServerUrl() {
    const host = (typeof location !== 'undefined' && location.hostname &&
                  location.hostname !== 'localhost' && location.hostname !== '127.0.0.1')
      ? location.hostname : 'localhost';
    return 'http://' + host + ':' + this.ports.voice;
  },
  get phoneServerUrl() {
    const host = (typeof location !== 'undefined' && location.hostname &&
                  location.hostname !== 'localhost' && location.hostname !== '127.0.0.1')
      ? location.hostname : 'localhost';
    return 'http://' + host + ':' + this.ports.phone;
  },
};

// Exposition globale
if (typeof window !== 'undefined') window.VITAL_KA_CONFIG = VITAL_KA_CONFIG;
if (typeof globalThis !== 'undefined') globalThis.VITAL_KA_CONFIG = VITAL_KA_CONFIG;

// ══════════════════════════════════════════════════════════════════════════
// Garde-fous globaux — un module défaillant ne doit jamais figer l'app
// ══════════════════════════════════════════════════════════════════════════
if (typeof window !== 'undefined') {
  window.addEventListener('unhandledrejection', (e) => {
    console.warn('[VitalKa] Promesse rejetée non gérée :', e.reason);
    e.preventDefault();   // évite le crash silencieux en production
  });
  window.addEventListener('error', (e) => {
    // Ne log que les erreurs de nos modules (pas les extensions navigateur)
    if (e.filename && !/^(https?:\/\/[^/]+)?\/(vital_ka|ka_)/.test(e.filename)) return;
    console.error('[VitalKa] Erreur :', e.message, '—', e.filename, ':', e.lineno);
  });
  console.log('[VitalKa] v' + VITAL_KA_CONFIG.version + ' — config chargée');
}
