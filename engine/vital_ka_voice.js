/* ══════════════════════════════════════════════════════════════════════════
   VITAL KA VOICE — Compagnon vocal (Phase 2 : Offline-first, Pont serveur)
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

  // ── Profils vocaux (surchargeables via vital_ka_config.js) ──
  const _cfg = (typeof VITAL_KA_CONFIG !== 'undefined') ? VITAL_KA_CONFIG : null;
  const _cfgVoice = (_cfg && _cfg.voice) || {};
  const _cfgProf = _cfgVoice.profiles || {};
  const PROFILES = {
    conseiller: { rate: (_cfgProf.conseiller && _cfgProf.conseiller.rate) || 1.0,  pitch: (_cfgProf.conseiller && _cfgProf.conseiller.pitch) || 1.0,  label: 'Conseiller soignant', voice: _cfgVoice.name || 'fr_FR-siwis-medium', speed: (_cfgProf.conseiller && _cfgProf.conseiller.speed) || 0.82 },
    compagnon:  { rate: (_cfgProf.compagnon && _cfgProf.compagnon.rate) || 0.88,  pitch: (_cfgProf.compagnon && _cfgProf.compagnon.pitch) || 1.05,  label: 'Compagnon patient',   voice: _cfgVoice.name || 'fr_FR-siwis-medium', speed: (_cfgProf.compagnon && _cfgProf.compagnon.speed) || 0.70 },
  };

  let _speaking = false;
  let _enabled = true;

  // ═══════════════════════════════════════════════════════════════
  // PHASE 2 — Pont vers le serveur KA PHONE (Piper TTS offline)
  // ═══════════════════════════════════════════════════════════════

  const server = {
    // URL auto-détectée : même IP que la page, port issu de vital_ka_config.js
    get url() {
      if (_cfg && _cfg.voiceServerUrl) return _cfg.voiceServerUrl;
      if (typeof location !== 'undefined' && location.hostname && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
        return 'http://' + location.hostname + ':8420';
      }
      return 'http://localhost:8420';
    },
    available: null,        // null = pas encore vérifié, true/false après détection
    _checking: false,       // éviter les détections parallèles
    _checkPromise: null,    // promesse de détection en cours
    _lastCheck: 0,          // timestamp du dernier check
    _checkTTL: 5000,        // re-vérifier toutes les 5 secondes (au lieu de 30s)
    _audioCtx: null,        // AudioContext pour lecture WAV (UNIQUE, partagé)
    _currentSource: null,   // source audio en cours (pour barge-in)
    _playQueue: [],         // file de lecture pour le streaming
    _playing: false,        // true si lecture audio en cours

    /**
     * Déverrouille l'AudioContext SYNCHRONEMENT dans la pile du geste utilisateur.
     * Indispensable : Chrome/Edge/Safari n'autorisent AudioContext.resume() QUE
     * pendant un geste utilisateur (clic, touche). Si on attend un fetch réseau
     * (~4s pour Piper) puis on tente resume(), le geste a expiré → silence.
     * Doit donc être appelé DIRECTEMENT depuis le handler onclick (pas après await).
     *
     * Technique robuste : on joue un tampon SILENCIEUX de 0 échantillon
     * synchrone­ment dans le geste. C'est la méthode reconnue pour forcer Chrome
     * à basculer le contexte en état 'running' AVANT tout travail async (fetch +
     * decodeAudioData). Sans ça, resume() peut résoudre trop tard et le source.start()
     * suivant est bloqué → silence malgré un serveur Piper détecté.
     * Idempotent. */
    unlock() {
      if (typeof window === 'undefined') return;
      if (!this._audioCtx) {
        const Ctx = window.AudioContext || window.webkitAudioContext;
        if (Ctx) this._audioCtx = new Ctx();
      }
      const ctx = this._audioCtx;
      if (!ctx) return;
      if (ctx.state === 'suspended') {
        // resume() renvoie une promesse ; on l'amorce sans await pour rester synchrone
        const p = ctx.resume();
        if (p && typeof p.catch === 'function') p.catch(() => {});
      }
      // Garde-fou supplémentaire : jouer du silence (1 sample) force le passage
      // en 'running' pendant le geste, même si resume() traîne.
      try {
        const buf = ctx.createBuffer(1, 1, ctx.sampleRate);
        const src = ctx.createBufferSource();
        src.buffer = buf;
        src.connect(ctx.destination);
        src.start(0);
      } catch (e) { /* silencieux : garde-fou best-effort */ }
    },

    /** Détecte si le serveur KA PHONE est accessible */
    async detect() {
      // Mode natif Android : pas de serveur Piper → Web Speech (voix système)
      if (_cfg && _cfg.voice && _cfg.voice.nativeMode) {
        this.available = false;
        return false;
      }
      const now = Date.now();
      // Cache : si vérifié il y a moins de _checkTTL, réutiliser
      if (this.available !== null && (now - this._lastCheck) < this._checkTTL) {
        return this.available;
      }
      // Éviter les appels parallèles
      if (this._checking && this._checkPromise) {
        return this._checkPromise;
      }
      this._checking = true;
      this._checkPromise = this._doDetect();
      try {
        const result = await this._checkPromise;
        return result;
      } finally {
        this._checking = false;
      }
    },

    async _doDetect() {
      this._lastCheck = Date.now();
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 2000);  // timeout plus long (2s)
        const resp = await fetch(this.url + '/api/voice/offline/caps', {
          signal: controller.signal,
          method: 'GET',
        });
        clearTimeout(timeout);
        if (resp.ok) {
          const caps = await resp.json();
          this.available = caps.offline_ready === true;
          if (this.available) {
            console.log('[KA_VOICE] ✅ Serveur détecté — Piper harmonique prêt (' +
              (caps.engines?.piper ? 'Piper' : '') +
              (caps.enhancements?.harmonic_post_processor ? ', boost φ' : '') + ')');
          } else {
            console.log('[KA_VOICE] ⚠️ Serveur présent mais Piper non disponible');
          }
          return this.available;
        }
        // Si le serveur répond mais pas OK, ne pas cacher — on réessaiera
        console.log('[KA_VOICE] ⚠️ Serveur injoignable (HTTP ' + resp.status + '), fallback Web Speech');
        this.available = false;
      } catch (e) {
        // Erreur réseau : ne pas mettre en cache négatif, le serveur peut démarrer
        console.log('[KA_VOICE] 🔄 Serveur non détecté (' + (e.name || 'network') + '), réessai au prochain speak()');
        return false;  // pas de cache négatif — on réessaiera au prochain appel
      }
      this.available = false;
      return false;
    },

    /** Récupère l'audio WAV depuis le serveur Piper */
    async fetchAudio(text, voice, speed) {
      if (!this.available) return null;
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 15000);
        const resp = await fetch(this.url + '/api/voice/offline', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, voice: voice || 'fr_FR-siwis-medium', speed: speed || 1.0, enhanced: true, hd: true }),
          signal: controller.signal,
        });
        clearTimeout(timeout);
        if (!resp.ok) return null;
        const arrayBuffer = await resp.arrayBuffer();
        if (arrayBuffer.byteLength < 100) return null;  // trop petit pour être valide
        return arrayBuffer;
      } catch (e) {
        console.warn('[KA_VOICE] Échec fetch audio:', e.message);
        return null;
      }
    },

    /** Joue un ArrayBuffer WAV via Web Audio API */
    async playAudio(arrayBuffer) {
      if (!arrayBuffer) {
        console.warn('[KA_VOICE] playAudio: arrayBuffer vide');
        return;
      }
      console.log('[KA_VOICE] playAudio: bytes=' + arrayBuffer.byteLength);
      // L'AudioContext doit déjà être déverrouillé par unlock() au moment du clic.
      if (!this._audioCtx) this.unlock();
      if (!this._audioCtx) {
        console.warn('[KA_VOICE] AudioContext indisponible (Web Audio non supporté)');
        return;
      }
      console.log('[KA_VOICE] playAudio: ctx.state=' + this._audioCtx.state + ' rate=' + this._audioCtx.sampleRate);
      // Au cas où le contexte serait suspendu (re-suspendu après longue inactivité)
      if (this._audioCtx.state === 'suspended') {
        await this._audioCtx.resume().catch(() => {});
      }
      try {
        const audioBuffer = await this._audioCtx.decodeAudioData(arrayBuffer.slice(0));
        console.log('[KA_VOICE] playAudio: décodé OK — dur=' + audioBuffer.duration.toFixed(2) + 's ch=' + audioBuffer.numberOfChannels + ' sr=' + audioBuffer.sampleRate);
        this.stopAudio();  // arrêter la lecture précédente
        const source = this._audioCtx.createBufferSource();
        source.buffer = audioBuffer;
        // Gain explicite à 1.0 (évite un mute involontaire sur certains navigateurs)
        const gain = this._audioCtx.createGain();
        gain.gain.value = 1.0;
        source.connect(gain);
        gain.connect(this._audioCtx.destination);
        source.onended = () => {
          console.log('[KA_VOICE] playAudio: lecture terminée (onended)');
          _speaking = false;
          this._playing = false;
          this._currentSource = null;
          _clearSpeakingButtons();
        };
        this._currentSource = source;
        this._playing = true;
        _speaking = true;
        source.start(0);
        console.log('[KA_VOICE] playAudio: source.start() appelé ✓');
      } catch (e) {
        console.warn('[KA_VOICE] Erreur lecture audio:', e.message, e.name);
        _speaking = false;
        this._playing = false;
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
  // l'événement 'voiceschanged'. On attend donc ce chargement (1.5 s max)
  // avant d'affirmer que la synthèse est indisponible.
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
    return _emitWebSpeech(text, profile);
  }

  /** Émission Web Speech SYNCCHRONE (partagée par _webSpeak et speakSync). */
  function _emitWebSpeech(text, profile) {
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
   * 1. Si serveur offline CONFIRMÉ dispo → Piper TTS (voix neuronale)
   * 2. Sinon → Web Speech API IMMÉDIAT (préserve le geste utilisateur)
   *
   * ⚠️ RÈGLE CRITIQUE (autoplay) : on n'attend JAMAIS une sonde réseau avant
   * le 1er speak(). Un `await fetch(...)` consomme le geste utilisateur du
   * clic 🔊 ; à l'expiration (2 s) Chrome refuse speechSynthesis → silence.
   * La détection serveur se fait en arrière-plan (via prewarm ou ci-dessous)
   * pour que l'appel SUIVANT puisse utiliser Piper.
   */
  async function speak(text, profile) {
    if (!isEnabled()) return false;
    if (!text || !String(text).trim()) return false;

    const p = PROFILES[profile] || PROFILES.conseiller;
    // Résolution dynamique de la voix : le sélecteur utilisateur prime sur le profil
    const voiceName = (_cfg && _cfg.voice && _cfg.voice.active) ? _cfg.voice.active : p.voice;

    // Mode natif Android : pas de serveur Piper → Web Speech immédiat
    // (préserve le geste utilisateur, voix système du téléphone)
    if (_cfg && _cfg.voice && _cfg.voice.nativeMode) {
      return _webSpeak(text, profile);
    }

    // Serveur déjà confirmé dispo → Piper neuronal (le geste reste valide,
    // fetchAudio est rapide et l'AudioContext est repris dans playAudio)
    if (server.available === true) {
      try {
        console.log('[KA_VOICE] 🎤 Piper — fetch audio en cours...');
        const audio = await server.fetchAudio(String(text).trim(), voiceName, p.speed);
        console.log('[KA_VOICE] 🎤 Piper — audio reçu:', audio ? audio.byteLength + ' octets' : 'NULL');
        if (audio) {
          await server.playAudio(audio);
          console.log('[KA_VOICE] 🎤 Piper — lecture lancée (ctx=' + (server._audioCtx ? server._audioCtx.state : 'null') + ')');
          return true;
        }
      } catch (e) {
        console.warn('[KA_VOICE] Serveur échoué, fallback Web Speech:', e.message);
        server.available = null;  // forcer réessai au prochain appel
      }
    }

    // Fallback Web Speech API — asynchrone (attente chargement voix WebView)
    const spoke = await _webSpeak(text, profile);

    // Détection en arrière-plan (fire-and-forget) : pas d'await ici,
    // pour ne pas retarder le retour ni consommer le geste. Le résultat
    // servira au prochain speak() si Piper est dispo.
    if (server.available === null && !server._checking) {
      server.detect().catch(() => {});
    }
    return spoke;
  }

  /** Version synchrone pour la compatibilité (utilise le cache de détection) */
  function speakSync(text, profile) {
    if (!isEnabled()) return false;
    if (!text || !String(text).trim()) return false;
    // Serveur confirmé dispo → Piper asynchrone (fire-and-forget)
    if (server.available === true) {
      speak(text, profile);
      return true;
    }
    // Fallback immédiat Web Speech (préserve le geste utilisateur).
    // ⚠️ _webSpeak est async : sans await elle retournerait une Promise —
    // speakSync doit rendre un booléen → émission synchrone directe.
    stop();
    if (!_voicesReady()) {
      // Voix pas encore chargées (WebView au démarrage) : émission différée,
      // retour optimiste (le contrat de speakSync reste booléen).
      _webSpeak(text, profile);
      return true;
    }
    const spoke = _emitWebSpeech(text, profile);
    if (server.available === null && !server._checking) {
      server.detect().catch(() => {});
    }
    return spoke;
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


/* ═══ Glue UI — VITAL KA (soignant) ═══ */

// Bouton 🔊 de l'écran IA : lit le dernier diagnostic (profil conseiller)
// IMPORTANT : unlock() SYNCHRONE au tout début — avant tout await — pour
// préserver le geste utilisateur exigé par Chrome pour AudioContext.resume().
async function aiSpeakLast() {
  KA_VOICE.server.unlock();           // geste valide ici (clic en cours)
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
  KA_VOICE.server.unlock();           // geste valide ici (clic en cours)
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
