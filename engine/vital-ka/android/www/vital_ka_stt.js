/**
 * Vital Ka STT — Reconnaissance Vocale (Speech-to-Text)
 * ======================================================
 * Utilise l'API Web Speech Recognition (intégrée à Chrome/Edge).
 * Fonctionne en français, gratuit, sans serveur.
 *
 * Architecture Push-to-Talk :
 *   start() → écoute continue → résultats intermédiaires → stop() → texte final
 *
 * États : 'idle' | 'listening' | 'error'
 *
 * Usage :
 *   KA_STT.onResult  = (text) => { ... };  // texte final reconnu
 *   KA_STT.onInterim = (text) => { ... };  // texte partiel (optionnel)
 *   KA_STT.onError   = (err)  => { ... };  // erreur
 *   KA_STT.start();
 *   KA_STT.stop();
 */

const KA_STT = (() => {
  'use strict';

  let _recognition = null;
  let _state = 'idle';           // 'idle' | 'listening' | 'error'
  let _finalText = '';           // texte accumulé final
  let _interimText = '';         // texte intermédiaire courant
  let _lang = 'fr-FR';
  let _continuous = true;        // écoute continue (push-to-talk)
  let _interimResults = true;    // résultats partiels
  let _restartTimer = null;      // redémarrage automatique après silence
  let _silenceTimeout = 8000;    // 8s de silence avant arrêt auto

  // ── Callbacks ──
  let _onResult  = null;         // function(text)
  let _onInterim = null;         // function(text)
  let _onError   = null;         // function({type, message})
  let _onState   = null;         // function(state)

  // ── API publique ──

  function isSupported() {
    // Mode natif Android : le wrapper KA_NATIVE_SR (vital_ka_native.js) émule
    // l'API Web Speech par-dessus le plugin Capacitor SpeechRecognizer.
    if (typeof window !== 'undefined' && window.KA_NATIVE_SR) return true;
    return typeof window !== 'undefined' &&
      ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);
  }

  function getState() { return _state; }

  /**
   * Démarre l'écoute. Appelé au début du push-to-talk.
   * @param {string} [lang='fr-FR'] - code langue BCP-47
   */
  function start(lang) {
    if (!isSupported()) {
      _setError('unsupported', 'SpeechRecognition non supporté sur ce navigateur.');
      return;
    }
    if (_state === 'listening') return;  // déjà en écoute

    if (lang) _lang = lang;
    _finalText = '';
    _interimText = '';

    if (!_recognition) {
      const Recog = window.KA_NATIVE_SR || window.SpeechRecognition || window.webkitSpeechRecognition;
      _recognition = new Recog();
      _recognition.continuous = _continuous;
      _recognition.interimResults = _interimResults;
      _recognition.lang = _lang;
      _recognition.maxAlternatives = 1;

      _recognition.onresult = _handleResult;
      _recognition.onerror  = _handleError;
      _recognition.onend    = _handleEnd;
      _recognition.onaudiostart = () => { /* son détecté */ };
      _recognition.onaudioend   = () => { /* silence */ };
      _recognition.onspeechstart = () => { /* parole début */ };
      _recognition.onspeechend   = () => { /* parole fin */ };
    } else {
      _recognition.lang = _lang;
    }

    try {
      _recognition.start();
      _setState('listening');
      _clearAutoStop();
    } catch (e) {
      // Déjà démarré ?
      if (e.name === 'InvalidStateError') {
        _recognition.stop();
        setTimeout(() => start(lang), 100);
        return;
      }
      _setError('start_error', e.message);
    }
  }

  /**
   * Arrête l'écoute et retourne le texte reconnu accumulé.
   * Appelé au relâchement du bouton push-to-talk.
   * @returns {string} texte final reconnu
   */
  function stop() {
    _clearAutoStop();
    if (!_recognition || _state !== 'listening') {
      _setState('idle');
      return _finalText || '';
    }
    try {
      _recognition.stop();
    } catch (e) {
      // ignore
    }
    _setState('idle');
    return _finalText || _interimText || '';
  }

  /** Annule l'écoute sans retourner de texte */
  function abort() {
    _clearAutoStop();
    if (_recognition) {
      try { _recognition.abort(); } catch (e) { /* ignore */ }
    }
    _finalText = '';
    _interimText = '';
    _setState('idle');
  }

  // ── Handlers internes ──

  function _handleResult(event) {
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
      _finalText += (_finalText ? ' ' : '') + final.trim();
    }
    _interimText = interim;

    // Callback texte final partiel (accumulé)
    if (_onResult && _finalText) {
      _onResult(_finalText + (interim ? ' ' + interim : ''));
    }
    // Callback texte intermédiaire
    if (_onInterim && interim) {
      _onInterim(interim);
    }

    // Réinitialiser le timer de silence après chaque résultat
    _resetAutoStop();
  }

  function _handleError(event) {
    // Ignorer 'no-speech' et 'aborted' — normaux en push-to-talk
    if (event.error === 'no-speech' || event.error === 'aborted') {
      if (_state === 'listening') {
        // Redémarrer automatiquement (l'utilisateur tient toujours le bouton)
        try { _recognition.start(); } catch (e) { /* ignore */ }
      }
      return;
    }
    if (event.error === 'not-allowed') {
      _setError('not_allowed', 'Accès au microphone refusé. Autorisez le micro dans les paramètres du navigateur.');
      return;
    }
    if (event.error === 'network') {
      _setError('network', 'Erreur réseau — la reconnaissance vocale nécessite une connexion.');
      return;
    }
    // Autres erreurs
    _setError(event.error, event.message || 'Erreur inconnue');
  }

  function _handleEnd() {
    // Si l'utilisateur a relâché (state !== 'listening'), ne pas redémarrer
    if (_state === 'listening') {
      // Reconnaissance terminée mais l'utilisateur tient toujours → redémarrer
      try {
        _recognition.start();
        _resetAutoStop();
      } catch (e) {
        // L'API peut rejeter le redémarrage rapide
        setTimeout(() => {
          if (_state === 'listening') {
            try { _recognition.start(); } catch (e2) { /* abandon */ }
          }
        }, 300);
      }
    }
  }

  function _setState(state) {
    _state = state;
    if (_onState) _onState(state);
  }

  function _setError(type, message) {
    _setState('error');
    if (_onError) _onError({ type, message });
    // Réinitialiser après 3s
    setTimeout(() => { if (_state === 'error') _setState('idle'); }, 3000);
  }

  // ── Timer de silence (arrêt automatique si l'utilisateur oublie de relâcher) ──

  function _resetAutoStop() {
    _clearAutoStop();
    _restartTimer = setTimeout(() => {
      if (_state === 'listening') {
        stop();
      }
    }, _silenceTimeout);
  }

  function _clearAutoStop() {
    if (_restartTimer) {
      clearTimeout(_restartTimer);
      _restartTimer = null;
    }
  }

  // ── Propriétés ──

  return {
    // Méthodes
    start, stop, abort, isSupported, getState,
    // Callbacks
    get onResult()  { return _onResult; },
    set onResult(fn) { _onResult = fn; },
    get onInterim()  { return _onInterim; },
    set onInterim(fn) { _onInterim = fn; },
    get onError()    { return _onError; },
    set onError(fn)  { _onError = fn; },
    get onState()    { return _onState; },
    set onState(fn)  { _onState = fn; },
    // Configuration
    get lang()           { return _lang; },
    set lang(v)          { _lang = v; },
    get silenceTimeout() { return _silenceTimeout; },
    set silenceTimeout(v) { _silenceTimeout = v; },
    // Accès direct au texte courant
    get currentText() { return _finalText + (_interimText ? ' ' + _interimText : ''); },
  };
})();
