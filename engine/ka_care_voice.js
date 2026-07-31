/* ══════════════════════════════════════════════════════════════════════════
   KA CARE VOICE — Compagnon vocal (Phase 2 : Offline-first, Pont serveur)
   ══════════════════════════════════════════════════════════════════════════
   Architecture :
     Phase 1 — Web Speech API (fallback ultime, 100% navigateur)
     Phase 2 — KA_VOICE.server → serveur local KA PHONE (Piper TTS offline)

   Stratégie offline-first :
     1. Détection automatique du serveur KA PHONE (localhost:8420)
     2. Si serveur dispo → TTS Piper (voix neuronale, 22 kHz, offline)
     3. Sinon → Web Speech API (robustesse maximale)

   Deux personae :
     🩺 conseiller — voix du soignant : lecture du diagnostic, mains libres
     🤗 compagnon  — voix du patient  : rappels médicaments, RDV, conseils

   Règle d'or : la voix est une couche de PRÉSENTATION. Elle lit exactement
   le texte validé par le moteur harmonique — zéro reformulation,
   zéro enrichissement aléatoire (aligné sur le principe zéro-hallucination).
   ══════════════════════════════════════════════════════════════════════════ */

const KA_VOICE = (() => {
  'use strict';

  // ── Profils vocaux (alignés sur vital_ka_voice.js — voix siwis validée) ──
  const PROFILES = {
    conseiller: { rate: 1.0,  pitch: 1.0,  label: 'Conseiller soignant', voice: 'fr_FR-siwis-medium', speed: 0.82 },
    compagnon:  { rate: 0.88, pitch: 1.05, label: 'Compagnon patient',   voice: 'fr_FR-siwis-medium', speed: 0.70 },
  };

  let _speaking = false;
  let _enabled = true;

  // ═══════════════════════════════════════════════════════════════
  // PHASE 2 — Pont vers le serveur KA PHONE (Piper TTS offline)
  // ═══════════════════════════════════════════════════════════════

  const server = {
    // URL auto-détectée : même IP que la page, port 8420 (serveur vocal)
    get url() {
      if (typeof location !== 'undefined' && location.hostname && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
        return 'http://' + location.hostname + ':8420';
      }
      return 'http://localhost:8420';
    },
    available: null,        // null = pas encore vérifié, true/false après détection
    _checking: false,       // éviter les détections parallèles
    _checkPromise: null,
    _lastCheck: 0,
    _checkTTL: 2000,
    _audioCtx: null,
    _currentSource: null,
    _playQueue: [],
    _playing: false,

    /** Détection simplifiée — toujours réessayer */
    async detect() {
      this._lastCheck = Date.now();
      try {
        const url = this.url + '/api/voice/offline/caps';
        console.log('[KA_VOICE] 🔍 Détection:', url);
        const resp = await fetch(url);
        if (resp.ok) {
          const caps = await resp.json();
          this.available = caps.offline_ready === true;
          console.log('[KA_VOICE]', this.available ? '✅ SERVEUR OK' : '⚠️ Serveur trouvé mais indisponible');
          return this.available;
        }
        console.log('[KA_VOICE] ⚠️ HTTP ' + resp.status);
        this.available = false;
      } catch (e) {
        console.log('[KA_VOICE] ❌ ' + (e.name || '?') + ': ' + (e.message || ''));
        this.available = false;
      }
      return false;
    },

    /** Récupère l'audio WAV depuis le serveur Piper */
    async fetchAudio(text, voice, speed) {
      if (!this.available) return null;
      try {
        console.log('[KA_VOICE] 📡 POST ' + this.url + '/api/voice/offline');
        const resp = await fetch(this.url + '/api/voice/offline', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, voice: voice || 'siwis', speed: speed || 1.0, enhanced: true }),
        });
        console.log('[KA_VOICE] 📡 Réponse: HTTP ' + resp.status + ', ' + resp.headers.get('Content-Type'));
        if (!resp.ok) return null;
        const arrayBuffer = await resp.arrayBuffer();
        if (arrayBuffer.byteLength < 100) return null;
        return arrayBuffer;
      } catch (e) {
        console.warn('[KA_VOICE] ❌ fetchAudio échec:', e.name, e.message);
        return null;
      }
    },

    /** Joue un ArrayBuffer WAV via Web Audio API */
    async playAudio(arrayBuffer) {
      if (!arrayBuffer) { console.log('[KA_VOICE] playAudio: pas de données'); return; }

      console.log('[KA_VOICE] 🔊 playAudio: ' + (arrayBuffer.byteLength/1024).toFixed(0) + ' Ko');

      // ── Méthode 1 : Web Audio API ──
      try {
        if (!this._audioCtx) {
          this._audioCtx = new (window.AudioContext || window.webkitAudioContext)();
          console.log('[KA_VOICE] AudioContext créé, state=' + this._audioCtx.state + ', rate=' + this._audioCtx.sampleRate);
        }
        const ctx = this._audioCtx;
        console.log('[KA_VOICE] AudioContext state=' + ctx.state);

        if (ctx.state === 'suspended') {
          console.log('[KA_VOICE] ▶️ Reprise AudioContext...');
          await ctx.resume();
          console.log('[KA_VOICE] AudioContext state après reprise=' + ctx.state);
        }

        console.log('[KA_VOICE] 🎼 Décodage audio...');
        const audioBuffer = await ctx.decodeAudioData(arrayBuffer.slice(0));
        console.log('[KA_VOICE] 🎼 Décodé: ' + audioBuffer.duration.toFixed(1) + 's, ' +
                    audioBuffer.sampleRate + 'Hz, ' + audioBuffer.numberOfChannels + 'ch');

        this.stopAudio();
        // ── Ajouter un GainNode pour booster le volume (×1.5) ──
        const gainNode = ctx.createGain();
        gainNode.gain.value = 1.5;  // +50% volume
        const source = ctx.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(gainNode);
        gainNode.connect(ctx.destination);
        source.onended = () => {
          console.log('[KA_VOICE] 🏁 Lecture Web Audio terminée');
          _speaking = false;
          this._playing = false;
          this._currentSource = null;
          _clearSpeakingButtons();
        };
        this._currentSource = source;
        this._playing = true;
        _speaking = true;
        source.start(0);
        console.log('[KA_VOICE] ▶️ Web Audio: start(0) appelé (gain=1.5)');
      } catch (e) {
        console.warn('[KA_VOICE] ⚠️ Web Audio échec:', e.name, e.message);
        // Continue vers le fallback <audio>
      }

      // ── Méthode 2 : élément <audio> visible (fallback + débogage) ──
      try {
        const blob = new Blob([arrayBuffer], { type: 'audio/wav' });
        const url = URL.createObjectURL(blob);
        let el = document.getElementById('ka-voice-audio');
        if (!el) {
          el = document.createElement('audio');
          el.id = 'ka-voice-audio';
          el.controls = true;
          el.style.cssText = 'position:fixed;bottom:10px;right:10px;z-index:9999;width:250px;background:#1a1a2e;border:1px solid #d4a853;border-radius:6px;padding:4px';
          el.title = '🔊 Sortie audio KA Care';
          document.body.appendChild(el);
        }
        el.src = url;
        el.volume = 1.0;
        el.onended = () => console.log('[KA_VOICE] 🏁 Lecture <audio> terminée');
        el.onerror = () => console.warn('[KA_VOICE] ⚠️ <audio> erreur');
        el.play().then(() => {
          console.log('[KA_VOICE] ▶️ <audio>: lecture démarrée (contrôles visibles en bas à droite)');
        }).catch(e => {
          console.warn('[KA_VOICE] ⚠️ <audio> play() rejeté:', e.message);
        });
      } catch (e) {
        console.warn('[KA_VOICE] ⚠️ <audio> fallback échec:', e.message);
      }
    },

    /** Arrête la lecture audio en cours (barge-in) */
    stopAudio() {
      if (this._currentSource) {
        try { this._currentSource.stop(); } catch (e) { /* déjà arrêté */ }
        this._currentSource = null;
      }
      this._playing = false;
      this._playQueue = [];
    },

    /** Streaming : découpe le texte en phrases et les joue séquentiellement */
    async playStream(text, voice, speed) {
      const sentences = _splitSentences(text);
      this.stopAudio();
      this._playQueue = [...sentences];
      await this._playNextInQueue(voice, speed);
    },

    async _playNextInQueue(voice, speed) {
      if (this._playQueue.length === 0) {
        this._playing = false;
        _speaking = false;
        _clearSpeakingButtons();
        return;
      }
      const sentence = this._playQueue.shift();
      const audio = await this.fetchAudio(sentence, voice, speed);
      if (audio && this._playQueue.length >= 0) {  // pas de barge-in entre-temps
        // Créer une promesse qui se résout quand la lecture est finie
        await new Promise((resolve) => {
          if (!this._audioCtx) {
            this._audioCtx = new (window.AudioContext || window.webkitAudioContext)();
          }
          if (this._audioCtx.state === 'suspended') {
            this._audioCtx.resume().then(() => {});
          }
          this._audioCtx.decodeAudioData(audio.slice(0), (buffer) => {
            if (this._playQueue.length === 0 && !this._playing) {
              resolve(); return;  // barge-in annulé
            }
            const source = this._audioCtx.createBufferSource();
            source.buffer = buffer;
            source.connect(this._audioCtx.destination);
            source.onended = () => {
              _speaking = (this._playQueue.length > 0);
              resolve();
            };
            this._currentSource = source;
            this._playing = true;
            _speaking = true;
            source.start(0);
          }, () => resolve());
        });
        // Jouer la phrase suivante
        if (this._playQueue.length > 0) {
          await this._playNextInQueue(voice, speed);
        } else {
          this._playing = false;
          _speaking = false;
          _clearSpeakingButtons();
        }
      }
    },
  };

  // ── Aide : découpage en phrases ──
  function _splitSentences(text) {
    const parts = String(text).split(/(?<=[.!?])\s+/);
    const result = [];
    for (let part of parts) {
      part = part.trim();
      if (!part) continue;
      if (part.length > 200) {
        const sub = part.split(/(?<=[,;:])\s+/);
        for (let s of sub) {
          s = s.trim();
          if (s) result.push(s);
        }
      } else {
        result.push(part);
      }
    }
    return result.length ? result : [String(text).trim()];
  }

  function _clearSpeakingButtons() {
    if (typeof document !== 'undefined') {
      document.querySelectorAll('.ka-voice-speaking')
        .forEach(b => b.classList.remove('ka-voice-speaking'));
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // PHASE 1 — Web Speech API (fallback)
  // ═══════════════════════════════════════════════════════════════

  let _voice = null;

  function isSupported() {
    return typeof window !== 'undefined' && 'speechSynthesis' in window;
  }

  function isEnabled() { return _enabled && isSupported(); }
  function setEnabled(on) { _enabled = !!on; if (!_enabled) stop(); }

  function _pickVoice() {
    if (_voice) return _voice;
    if (!isSupported()) return null;
    const all = speechSynthesis.getVoices() || [];
    // Filtrer : voix françaises uniquement (fr-FR, fr-BE, fr-CA, fr_CH, fr_XX)
    const fr = all.filter(v => v.lang && v.lang.toLowerCase().replace('_', '-').startsWith('fr'));

    // ── Hiérarchie de qualité vocale ──
    // Tier 1 ★★★ Microsoft Edge Natural (Hortense/Denise/Henri) — Windows 10/11
    //        Ces voix sont neuronales, 24 kHz, avec prosodie naturelle.
    _voice = fr.find(v => /microsoft.*(hortense|denise|henri)/i.test(v.name));
    if (_voice) { console.log('[KA_VOICE] ✅ Voix Edge Natural: ' + _voice.name); return _voice; }

    // Tier 2 ★★ Toute voix Natural/Neural/Online (Google, Apple, Amazon, MS générique)
    _voice = fr.find(v => /natural|neural|online/i.test(v.name));
    if (_voice) { console.log('[KA_VOICE] ✅ Voix Neural: ' + _voice.name); return _voice; }

    // Tier 3 ★ Voices Premium/Enhanced/WaveNet
    _voice = fr.find(v => /premium|enhanced|wavenet/i.test(v.name));
    if (_voice) { console.log('[KA_VOICE] ⚠️ Voix Premium: ' + _voice.name); return _voice; }

    // Tier 4 — Dernier recours : première voix française dispo (souvent robotique)
    _voice = fr[0] || null;
    if (_voice) console.log('[KA_VOICE] ⚠️ Fallback voix FR: ' + _voice.name);
    return _voice;
  }
  if (isSupported()) {
    speechSynthesis.onvoiceschanged = () => { _voice = null; _pickVoice(); };
    _pickVoice();
  }

  // Sur WebView Android (Capacitor), getVoices() est vide au démarrage :
  // les voix du moteur TTS système se chargent de façon ASYNCHRONE via
  // l'événement 'voiceschanged'. On attend ce chargement (1.5 s max).
  function _voicesReady() {
    if (!isSupported()) return false;
    const all = speechSynthesis.getVoices() || [];
    return all.length > 0;
  }
  function _waitForVoices(timeoutMs) {
    return new Promise(resolve => {
      if (_voicesReady()) return resolve(true);
      let done = false;
      const finish = (ok) => { if (done) return; done = true; resolve(ok); };
      try { speechSynthesis.onvoiceschanged = () => { _voice = null; _pickVoice(); finish(_voicesReady()); }; } catch (e) {}
      setTimeout(() => finish(_voicesReady()), timeoutMs || 1500);
    });
  }

  async function _webSpeak(text, profile) {
    if (!isSupported()) return false;
    if (!text || !String(text).trim()) return false;
    stop();
    // Si aucune voix encore chargée (WebView Android au démarrage), attendre
    if (!_voicesReady()) {
      const ok = await _waitForVoices(1500);
      if (!ok) {
        console.warn('[KA_VOICE] Aucune voix TTS disponible après attente');
        return false;
      }
    }
    const p = PROFILES[profile] || PROFILES.conseiller;
    const u = new SpeechSynthesisUtterance(String(text).trim());
    u.lang = 'fr-FR';
    u.rate = p.rate;
    u.pitch = p.pitch;
    u.volume = 1.0;
    const v = _pickVoice();
    if (v) u.voice = v;
    _speaking = true;
    u.onend = () => { _speaking = false; _clearSpeakingButtons(); };
    u.onerror = () => { _speaking = false; _clearSpeakingButtons(); };
    speechSynthesis.speak(u);
    return true;
  }

  // ═══════════════════════════════════════════════════════════════
  // API UNIFIÉE — route automatiquement serveur vs Web Speech
  // ═══════════════════════════════════════════════════════════════

  /**
   * speak() — point d'entrée unique.
   * 1. Si serveur offline détecté → Piper TTS (voix neuronale)
   * 2. Sinon → Web Speech API (robustesse)
   */
  async function speak(text, profile) {
    if (!isEnabled()) { console.log('[KA_VOICE] speak: désactivé'); return false; }
    if (!text || !String(text).trim()) { console.log('[KA_VOICE] speak: texte vide'); return false; }

    const p = PROFILES[profile] || PROFILES.conseiller;
    console.log('[KA_VOICE] 🎤 speak() appelé — texte: ' + String(text).substring(0, 60) + '...');

    // Mode natif Android : pas de serveur Piper → Web Speech immédiat
    // (évite le await detect() qui bloquerait sur un serveur absent)
    const _native = (typeof VITAL_KA_CONFIG !== 'undefined' &&
                     VITAL_KA_CONFIG.platform && VITAL_KA_CONFIG.platform.isNative);
    if (_native) {
      console.log('[KA_VOICE] 📱 Mode natif → Web Speech (voix système)');
      return _webSpeak(text, profile);
    }

    // Toujours re-détecter
    console.log('[KA_VOICE] → detect()...');
    const ready = await server.detect();
    console.log('[KA_VOICE] → detect() = ' + ready + ', server.available = ' + server.available);

    if (ready && server.available === true) {
      console.log('[KA_VOICE] → fetchAudio()...');
      try {
        const audio = await server.fetchAudio(String(text).trim(), p.voice, p.speed);
        console.log('[KA_VOICE] → fetchAudio() = ' + (audio ? (audio.byteLength + ' bytes') : 'null'));
        if (audio) {
          console.log('[KA_VOICE] → playAudio()...');
          await server.playAudio(audio);
          console.log('[KA_VOICE] ✅ PIPER HARMONIQUE — SUCCÈS');
          return true;
        }
      } catch (e) {
        console.warn('[KA_VOICE] ❌ Erreur serveur:', e.message);
        server.available = null;
      }
    }

    // Fallback
    console.log('[KA_VOICE] 🔽 Fallback Web Speech API');
    return _webSpeak(text, profile);
  }

  /** Version synchrone pour la compatibilité (utilise le cache de détection) */
  function speakSync(text, profile) {
    if (!isEnabled()) return false;
    if (!text || !String(text).trim()) return false;
    // Si le serveur était dispo lors du dernier check, tenter async
    if (server.available === true) {
      speak(text, profile);  // fire-and-forget
      return true;
    }
    return _webSpeak(text, profile);
  }

  function stop() {
    // Arrêter le serveur
    server.stopAudio();
    // Arrêter la Web Speech API
    if (isSupported()) speechSynthesis.cancel();
    _speaking = false;
    server._playing = false;
    _clearSpeakingButtons();
  }

  function isSpeaking() { return _speaking || server._playing; }

  // ═══════════════════════════════════════════════════════════════
  // TEXTE MÉDICAL STRUCTURÉ — STRICTEMENT déterministe
  // ═══════════════════════════════════════════════════════════════

  function buildDiagnosisSpeech(diag) {
    if (!diag || !diag.top) return '';
    const t = diag.top;
    const parts = [];
    const score = (typeof t.score === 'number') ? t.score : 0;
    const pct = score <= 1 ? Math.round(score * 100) : Math.round(score);
    parts.push('Diagnostic probable : ' + t.name + ', confiance ' + pct + ' pour cent.');
    if (t.g) parts.push('Gravité : ' + t.g + '.');
    if (t.u) parts.push('Attention, situation urgente.');
    if (t.c) parts.push('Conduite à tenir : ' + t.c);
    if (t.d) parts.push('Délai de consultation : ' + t.d + '.');
    parts.push('Rappel : ceci est une aide au diagnostic, et non un avis médical définitif.');
    // ── Phytothérapie complémentaire (déterministe) ──
    if (typeof Knowledge === 'object' && Knowledge && Knowledge.getPhytoFor && diag.top) {
      try {
        const plants = Knowledge.getPhytoFor([diag.top.name]);
        if (plants && plants.length) {
          const ab = plants.filter(p => p.grade_evidence === 'A' || p.grade_evidence === 'B');
          const cCount = plants.filter(p => p.grade_evidence === 'C' && p.niveau_recommandation !== 'vigilance').length;
          const vigCount = plants.filter(p => p.niveau_recommandation === 'vigilance').length;
          if (ab.length) {
            const names = ab.slice(0, 3).map(p => p.nom_scientifique + ' (grade ' + p.grade_evidence + ')').join(', ');
            parts.push('Plantes traditionnelles associées : ' + names + '.');
          }
          if (cCount) parts.push('Autres usages traditionnels documentés : ' + cCount + ' plante' + (cCount > 1 ? 's' : '') + ' de grade C.');
          if (vigCount) parts.push('Attention : ' + vigCount + ' plante' + (vigCount > 1 ? 's' : '') + ' toxique' + (vigCount > 1 ? 's' : '') + ' à éviter.');
          parts.push('Rappel : la phytothérapie ne remplace pas le traitement de référence.');
        }
      } catch (e) { /* silencieux */ }
    }
    return parts.join(' ');
  }

  /** Lit le dernier diagnostic (async — tente le serveur d'abord) */
  async function speakLastDiagnosis(profile) {
    const diag = (typeof getLastDiagnosis === 'function') ? getLastDiagnosis() : null;
    if (!diag) {
      return speak("Aucun diagnostic disponible. Lancez d'abord une analyse.", profile || 'conseiller');
    }
    return speak(buildDiagnosisSpeech(diag), profile || 'conseiller');
  }

  /** Pré-chauffe la détection du serveur (à appeler au démarrage) */
  function prewarm() {
    server.detect().catch(() => {});
  }

  return {
    PROFILES, server,
    isSupported, isEnabled, setEnabled,
    speak, speakSync, stop, isSpeaking,
    buildDiagnosisSpeech, speakLastDiagnosis,
    prewarm,
  };
})();


/* ═══ Glue UI — KA CARE (soignant) ═══ */

// Bouton 🔊 de l'écran IA : lit le dernier diagnostic (profil conseiller)
async function aiSpeakLast() {
  const ok = await KA_VOICE.speakLastDiagnosis('conseiller');
  if (typeof aiAddMessage === 'function') {
    aiAddMessage(ok
      ? '🔊 Lecture vocale du diagnostic (mode ' + (KA_VOICE.server.available ? 'Piper neuronal + boost φ' : 'navigateur') + ').'
      : '🔇 Synthèse vocale indisponible sur cet appareil.', 'system');
  }
}

// Bouton 🔊 de la carte résultat (même action, hors écran IA)
async function speakDiagnosisResult(btn) {
  if (KA_VOICE.isSpeaking()) { KA_VOICE.stop(); return; }
  const ok = await KA_VOICE.speakLastDiagnosis('conseiller');
  if (ok && btn && btn.classList) btn.classList.add('ka-voice-speaking');
}

// Stop global
function voiceStop() { KA_VOICE.stop(); }

// Pré-chauffage au chargement
if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => KA_VOICE.prewarm(), 500);
  });
}
