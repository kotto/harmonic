/**
 * Vital Ka CONVERSATION — Dialogue Vocal Naturel (Full Duplex)
 * ==============================================================
 * Conversation naturelle sans push-to-talk :
 *   - Toujours en écoute (activation par toggle)
 *   - Détection automatique de fin de parole (silence 1.5s)
 *   - Barge-in : l'utilisateur peut interrompre l'IA
 *   - STT navigateur (Web Speech API) + fallback ka_phone Whisper
 *   - TTS via serveur Piper local (:8420)
 *   - IA via backend /api/ask (:8421) si dispo, sinon IA locale
 *
 * États : 'idle' | 'listening' | 'thinking' | 'speaking'
 *
 * Usage :
 *   KA_CONVERSATION.toggle();  // active/désactive l'écoute continue
 *   KA_CONVERSATION.setMode('conseiller'); // ou 'compagnon'
 */

const KA_CONVERSATION = (() => {
  'use strict';

  // ── Configuration ──
  const CONFIG = {
    silenceThreshold: 1800,    // ms de silence avant de considérer la phrase terminée
    maxListeningTime: 15000,   // temps max d'écoute continue (sécurité)
    kaPhonePort: 8421,         // port du serveur ka_phone (STT Whisper + AI)
    piperPort: 8420,           // port du serveur Piper TTS
  };

  // ── État ──
  let _mode = 'conseiller';    // 'conseiller' | 'compagnon'
  let _state = 'idle';         // 'idle' | 'listening' | 'thinking' | 'speaking'
  let _active = false;         // toggle on/off
  let _recognition = null;     // instance SpeechRecognition
  let _silenceTimer = null;    // timeout de silence
  let _maxListenTimer = null;  // timeout de sécurité
  let _finalTranscript = '';   // texte accumulé final
  let _interimTranscript = ''; // texte intermédiaire
  let _currentAudio = null;    // élément Audio en cours de lecture
  let _conversationHistory = []; // historique de la conversation
  let _kaPhoneAvailable = null;  // null=pas vérifié, true/false

  // ── Callbacks ──
  let _onStateChange = null;   // function(state, mode)
  let _onTranscript = null;    // function(text, isFinal)

  // ═══════════════════════════════════════════════════════════════
  // API PUBLIQUE
  // ═══════════════════════════════════════════════════════════════

  function getState() { return _state; }
  function getMode()  { return _mode; }
  function isActive() { return _active; }

  /** Active ou désactive l'écoute continue */
  async function toggle() {
    if (_active) {
      deactivate();
    } else {
      await activate();
    }
  }

  /** Active l'écoute continue */
  async function activate() {
    if (_active) return;

    // Vérifier support STT
    if (!isSTTSupported()) {
      _notify('⚠️ Reconnaissance vocale non supportée. Utilisez Chrome ou Edge.', 'system');
      return false;
    }

    // Demander la permission micro
    try {
      await requestMicrophone();
    } catch (e) {
      _notify('⚠️ Accès au microphone refusé. Autorisez-le dans les paramètres.', 'system');
      return false;
    }

    // Déverrouiller l'AudioContext (prérequis TTS)
    if (typeof KA_VOICE !== 'undefined' && KA_VOICE.server) {
      KA_VOICE.server.unlock();
    }

    _active = true;
    _conversationHistory = [];
    _setState('listening');
    _startListening();
    _updateUI();

    _notify('🟢 **Conversation active** — Je vous écoute. Parlez naturellement.', 'system');

    // Vérifier la disponibilité du serveur ka_phone en arrière-plan
    _checkKaPhone();

    return true;
  }

  /** Désactive l'écoute continue */
  function deactivate() {
    _active = false;
    _stopListening();
    _clearTimers();
    _stopAudio();
    _setState('idle');
    _updateUI();
    _notify('⚪ Conversation arrêtée.', 'system');
  }

  /** Change le mode (conseiller/compagnon) */
  function setMode(mode) {
    _mode = mode === 'compagnon' ? 'compagnon' : 'conseiller';
    _updateUI();
    const label = _mode === 'conseiller'
      ? '🩺 Mode **Conseiller** actif — Réponses techniques, diagnostic.'
      : '🤗 Mode **Compagnon** actif — Explications simples, conseils.';
    _notify(label, 'system');
  }

  function toggleMode() {
    setMode(_mode === 'conseiller' ? 'compagnon' : 'conseiller');
  }

  // ═══════════════════════════════════════════════════════════════
  // STT — Reconnaissance Vocale Continue
  // ═══════════════════════════════════════════════════════════════

  function isSTTSupported() {
    if (typeof window !== 'undefined' && window.KA_NATIVE_SR) return true;
    return typeof window !== 'undefined' &&
      ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);
  }

  async function requestMicrophone() {
    // getUserMedia force la demande de permission
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    // Arrêter immédiatement — on utilise SpeechRecognition, pas MediaRecorder
    stream.getTracks().forEach(t => t.stop());
  }

  function _startListening() {
    if (!_active) return;
    if (_recognition) {
      try { _recognition.abort(); } catch (e) { /* ignore */ }
    }

    const Recog = window.KA_NATIVE_SR || window.SpeechRecognition || window.webkitSpeechRecognition;
    _recognition = new Recog();
    _recognition.continuous = true;
    _recognition.interimResults = true;
    _recognition.lang = 'fr-FR';
    _recognition.maxAlternatives = 1;

    _finalTranscript = '';
    _interimTranscript = '';

    _recognition.onresult = (event) => {
      let interim = '';
      let final = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          final += result[0].transcript;
        } else {
          interim += result[0].transcript;
        }
      }

      if (final) {
        _finalTranscript += (_finalTranscript ? ' ' : '') + final.trim();
      }
      _interimTranscript = interim;

      const displayText = _finalTranscript + (interim ? ' ' + interim : '');
      if (_onTranscript) _onTranscript(displayText, !interim);

      // Mettre à jour l'affichage dans le chat
      _updateInterimDisplay(displayText);

      // Réinitialiser le timer de silence à chaque parole détectée
      _resetSilenceTimer();

      // Si on était en train de parler (barge-in), arrêter l'audio
      if (_state === 'speaking') {
        _bargeIn();
      }
    };

    _recognition.onspeechstart = () => {
      // Barge-in : l'utilisateur parle pendant que l'IA répond
      if (_state === 'speaking') {
        _bargeIn();
      }
    };

    _recognition.onerror = (event) => {
      if (event.error === 'no-speech') {
        // Normal : juste du silence, on continue
        return;
      }
      if (event.error === 'aborted') {
        // Normal : on a arrêté volontairement
        return;
      }
      if (event.error === 'not-allowed') {
        _notify('⚠️ Micro non autorisé.', 'system');
        deactivate();
        return;
      }
      if (event.error === 'network') {
        // Le STT navigateur a besoin du réseau — réessayer
        if (_active) {
          setTimeout(() => { if (_active) _restartRecognition(); }, 1000);
        }
        return;
      }
      // Autres erreurs : réessayer
      if (_active) {
        setTimeout(() => { if (_active) _restartRecognition(); }, 500);
      }
    };

    _recognition.onend = () => {
      // Si toujours actif, redémarrer (l'API s'arrête après un certain temps)
      if (_active && _state !== 'thinking') {
        _restartRecognition();
      }
    };

    try {
      _recognition.start();
      _resetSilenceTimer();
      _resetMaxListenTimer();
    } catch (e) {
      if (e.name === 'InvalidStateError') {
        // Déjà démarré
        _recognition.stop();
        setTimeout(() => _startListening(), 200);
        return;
      }
      console.warn('[KA_CONVERSATION] Erreur démarrage STT:', e.message);
    }
  }

  function _stopListening() {
    if (_recognition) {
      try { _recognition.abort(); } catch (e) { /* ignore */ }
      _recognition = null;
    }
    _clearTimers();
  }

  function _restartRecognition() {
    if (!_active) return;
    try {
      if (_recognition) {
        _recognition.start();
      } else {
        _startListening();
      }
    } catch (e) {
      // L'API peut refuser un redémarrage trop rapide
      setTimeout(() => {
        if (_active) _startListening();
      }, 300);
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // SILENCE DETECTION & TRAITEMENT
  // ═══════════════════════════════════════════════════════════════

  function _resetSilenceTimer() {
    if (_silenceTimer) clearTimeout(_silenceTimer);
    _silenceTimer = setTimeout(() => {
      if (_finalTranscript.trim() && _state === 'listening') {
        _handleUserSpeech(_finalTranscript.trim());
      }
    }, CONFIG.silenceThreshold);
  }

  function _resetMaxListenTimer() {
    if (_maxListenTimer) clearTimeout(_maxListenTimer);
    _maxListenTimer = setTimeout(() => {
      if (_state === 'listening') {
        // Forcer l'envoi même si pas de silence (sécurité)
        if (_finalTranscript.trim()) {
          _handleUserSpeech(_finalTranscript.trim());
        } else {
          // Redémarrer l'écoute
          _stopListening();
          if (_active) _startListening();
        }
      }
    }, CONFIG.maxListeningTime);
  }

  function _clearTimers() {
    if (_silenceTimer) { clearTimeout(_silenceTimer); _silenceTimer = null; }
    if (_maxListenTimer) { clearTimeout(_maxListenTimer); _maxListenTimer = null; }
  }

  // ═══════════════════════════════════════════════════════════════
  // TRAITEMENT DE LA PAROLE
  // ═══════════════════════════════════════════════════════════════

  async function _handleUserSpeech(text) {
    if (!text || !text.trim()) return;

    _setState('thinking');
    _stopListening();  // pause STT pendant le traitement

    // Afficher dans le chat
    _notify('🎤 ' + text, 'user');

    // Ajouter à l'historique
    _conversationHistory.push({ role: 'user', content: text });

    // Obtenir la réponse
    let response;
    try {
      response = await _getAIResponse(text);
    } catch (e) {
      response = "Désolé, je n'ai pas pu traiter votre demande. Pouvez-vous reformuler ?";
    }

    if (response) {
      // Afficher la réponse
      const icon = _mode === 'conseiller' ? '🩺' : '🤗';
      _notify(icon + ' ' + response, 'ai');
      _conversationHistory.push({ role: 'assistant', content: response });

      // Synthèse vocale
      _setState('speaking');
      await _speakResponse(response);
    }

    // Reprendre l'écoute
    if (_active) {
      _finalTranscript = '';
      _interimTranscript = '';
      _setState('listening');
      _startListening();
    }
  }

  async function _getAIResponse(text) {
    // Essayer le backend ka_phone si disponible
    if (_kaPhoneAvailable === true) {
      try {
        const resp = await _callKaPhone(text);
        if (resp) return resp;
      } catch (e) {
        _kaPhoneAvailable = false;  // marquer indisponible
      }
    }

    // Fallback : IA locale (vital_ka_ai.js)
    return _getLocalAIResponse(text);
  }

  async function _callKaPhone(text) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    const resp = await fetch(`http://localhost:${CONFIG.kaPhonePort}/api/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: text,
        context: _conversationHistory.slice(-5).map(m => m.content).join('\n'),
        style: _mode === 'compagnon' ? 'chaleureux' : 'concise',
      }),
      signal: controller.signal,
    });
    clearTimeout(timeout);
    if (resp.ok) {
      const data = await resp.json();
      return data.response || data.text || data.answer || null;
    }
    return null;
  }

  function _getLocalAIResponse(text) {
    // Utiliser les fonctions IA locales
    if (_mode === 'conseiller') {
      return _localConseillerResponse(text);
    } else {
      return _localCompagnonResponse(text);
    }
  }

  function _localConseillerResponse(text) {
    // Réutiliser la logique de KA_DIALOGUE pour le mode conseiller
    if (typeof KA_DIALOGUE !== 'undefined') {
      // Accéder aux fonctions internes via une méthode exposée
      // (on duplique la logique ici pour l'autonomie)
    }

    const q = text.toLowerCase();

    // Diagnostic
    if (q.includes('diagnostic') || q.includes('explique') || q.includes('résultat')) {
      const diag = _getDiagnosis();
      if (diag && typeof kaAI !== 'undefined' && kaAI.explain) {
        const holo = typeof buildCurrentHologram === 'function' ? buildCurrentHologram() : null;
        return kaAI.explain(diag.top, holo, diag.pVec);
      }
      return "Aucun diagnostic en cours. Lancez d'abord une analyse depuis l'écran Résonance.";
    }

    // Plantes
    if (q.includes('plante') || q.includes('phyto') || q.includes('traditionnel')) {
      const diag = _getDiagnosis();
      if (diag && typeof Knowledge !== 'undefined' && Knowledge.getPhytoFor) {
        try {
          const plants = Knowledge.getPhytoFor([diag.top.name], diag.pVec || null);
          if (plants && plants.length) {
            let text = '🌿 **Plantes pour ' + diag.top.name + '** :\n';
            plants.filter(p => p.grade_evidence === 'A' || p.grade_evidence === 'B')
              .slice(0, 5).forEach(p => {
                text += `- ${p.nom_scientifique} — ${p.partie_utilisee} · ${p.preparation}\n`;
              });
            return text;
          }
        } catch (e) { /* ignore */ }
      }
    }

    // Recherche médicale
    if (typeof kaAI !== 'undefined' && kaAI && kaAI.searchMedical) {
      try { return kaAI.searchMedical(text); } catch (e) { /* ignore */ }
    }

    return "Je vous écoute. Décrivez les symptômes ou posez une question médicale précise.";
  }

  function _localCompagnonResponse(text) {
    const q = text.toLowerCase();

    if (q.includes('bonjour') || q.includes('salut')) {
      return 'Bonjour ! Je suis votre compagnon Vital Ka. Comment puis-je vous aider à prendre soin de votre santé aujourd\'hui ? 🌿';
    }
    if (q.includes('merci')) {
      return 'Avec plaisir ! Prenez soin de vous. 🌿';
    }
    if (q.includes('qui es') || q.includes('tu es')) {
      return 'Je suis votre **compagnon de santé**, un assistant qui vous aide à comprendre votre état de santé avec des mots simples. Je peux vous parler des plantes médicinales, vous donner des conseils, et vous orienter vers un médecin si nécessaire.';
    }

    const diag = _getDiagnosis();
    if (diag && (q.includes('explique') || q.includes('comprendre') || q.includes('c\'est quoi'))) {
      const t = diag.top;
      const pct = Math.round((t.score || 0) * 100);
      return `D'après les symptômes, il pourrait s'agir de **${t.name.replace(/_/g, ' ')}** (confiance ${pct}%). ${t.c || ''} Ne vous inquiétez pas, cela se traite bien. Consultez dans un délai ${(t.d || 'raisonnable').toLowerCase()}.`;
    }

    if (_looksLikeSymptoms(text)) {
      return "Ces symptômes méritent attention. Je vous invite à les faire analyser dans l'écran Résonance (🔍) pour un diagnostic précis. En attendant, reposez-vous et buvez beaucoup d'eau. Si la fièvre est élevée ou si vous avez des douleurs intenses, consultez rapidement.";
    }

    return "Je vous écoute. Décrivez ce qui vous préoccupe, je ferai de mon mieux pour vous aider. 🌿";
  }

  function _getDiagnosis() {
    if (typeof getLastDiagnosis === 'function') return getLastDiagnosis();
    return null;
  }

  function _looksLikeSymptoms(text) {
    const words = ['mal', 'douleur', 'fièvre', 'tousse', 'vomi', 'diarrhée', 'fatigue', 'maux', 'courbature', 'frisson', 'saigne'];
    return words.some(w => text.toLowerCase().includes(w));
  }

  // ═══════════════════════════════════════════════════════════════
  // TTS — Synthèse Vocale + Barge-in
  // ═══════════════════════════════════════════════════════════════

  async function _speakResponse(text) {
    // Arrêter tout audio en cours
    _stopAudio();

    // Utiliser KA_VOICE (Piper)
    if (typeof KA_VOICE !== 'undefined' && KA_VOICE.speak) {
      try {
        await KA_VOICE.speak(text, _mode);
      } catch (e) {
        console.warn('[KA_CONVERSATION] Erreur TTS:', e.message);
        _fallbackTTS(text);
      }
    } else {
      _fallbackTTS(text);
    }
  }

  function _fallbackTTS(text) {
    // Web Speech API fallback
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = 'fr-FR';
      u.rate = _mode === 'compagnon' ? 0.85 : 0.95;
      u.onend = () => {
        if (_state === 'speaking' && _active) {
          _setState('listening');
        }
      };
      speechSynthesis.cancel();
      speechSynthesis.speak(u);
    }
  }

  function _stopAudio() {
    // Arrêter la lecture audio HTML5
    if (_currentAudio) {
      try { _currentAudio.pause(); _currentAudio = null; } catch (e) { /* ignore */ }
    }
    // Arrêter le TTS via KA_VOICE
    if (typeof KA_VOICE !== 'undefined' && KA_VOICE.stop) {
      KA_VOICE.stop();
    }
    // Arrêter le Web Speech
    if (typeof speechSynthesis !== 'undefined') {
      speechSynthesis.cancel();
    }
  }

  /** Barge-in : l'utilisateur interrompt l'IA */
  function _bargeIn() {
    _stopAudio();
    _finalTranscript = '';
    _interimTranscript = '';
    _setState('listening');
    _notify('🔄 Je vous écoute...', 'system');

    // Notifier le serveur ka_phone si dispo
    if (_kaPhoneAvailable) {
      fetch(`http://localhost:${CONFIG.kaPhonePort}/api/speech/barge-in`, { method: 'POST' })
        .catch(() => {});
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // UI
  // ═══════════════════════════════════════════════════════════════

  function _setState(state) {
    _state = state;
    if (_onStateChange) _onStateChange(state, _mode);
    _updateUI();
  }

  function _updateUI() {
    if (typeof document === 'undefined') return;
    const toggle = document.getElementById('conversationToggle');
    const status = document.getElementById('conversationStatus');
    const modeBtn = document.getElementById('voiceModeBtn2');

    if (toggle) {
      const stateLabels = {
        idle: '🎤 Conversation arrêtée',
        listening: '🟢 À l\'écoute...',
        thinking: '⏳ Je réfléchis...',
        speaking: '🔊 Je vous réponds...',
      };
      toggle.textContent = stateLabels[_state] || stateLabels.idle;
      toggle.className = 'conv-toggle ' + _state;
    }
    if (status) {
      const statusLabels = {
        idle: 'Cliquez pour démarrer la conversation',
        listening: 'Parlez naturellement — je vous écoute',
        thinking: 'Analyse de votre demande en cours...',
        speaking: 'Réponse vocale en cours...',
      };
      status.textContent = statusLabels[_state] || statusLabels.idle;
    }
    if (modeBtn) {
      modeBtn.textContent = _mode === 'conseiller' ? '🩺 Conseiller' : '🤗 Compagnon';
      modeBtn.className = 'mode-btn ' + _mode;
    }
  }

  function _updateInterimDisplay(text) {
    if (typeof document === 'undefined') return;
    const el = document.getElementById('interimText');
    if (el) {
      el.textContent = text || '';
      el.style.display = text ? 'block' : 'none';
    }
  }

  function _notify(text, role) {
    if (typeof aiAddMessage === 'function') {
      aiAddMessage(text, role || 'system');
    }
  }

  async function _checkKaPhone() {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 3000);
      const resp = await fetch(`http://localhost:${CONFIG.kaPhonePort}/api/speech/capabilities`, {
        signal: controller.signal,
      });
      clearTimeout(timeout);
      _kaPhoneAvailable = resp.ok;
    } catch (e) {
      _kaPhoneAvailable = false;
    }
  }

  // ── Init ──
  if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => _updateUI(), 800);
    });
  }

  return {
    toggle, activate, deactivate,
    setMode, toggleMode,
    getState, getMode, isActive,
    get onStateChange() { return _onStateChange; },
    set onStateChange(fn) { _onStateChange = fn; },
    get onTranscript() { return _onTranscript; },
    set onTranscript(fn) { _onTranscript = fn; },
  };
})();
