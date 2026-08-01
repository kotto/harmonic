/* ══════════════════════════════════════════════════════════════════════════
   VITAL KA — Adaptateur Natif Android (Capacitor)
   ══════════════════════════════════════════════════════════════════════════
   Chargé APRÈS vital_ka_config.js dans vital_ka.html et ka_patient.html.

   Rôle :
   1. Détecte l'exécution dans la WebView native (window.Capacitor).
   2. Expose window.KA_NATIVE_SR — classe émulant l'API Web Speech
      (SpeechRecognition) par-dessus le plugin natif
      @capacitor-community/speech-recognition (SpeechRecognizer Android).

   Hors Capacitor (navigateur PC) : ce fichier ne fait RIEN.

   Sémantique du plugin natif (vérifiée dans le source Java v7) :
   - start({partialResults:true}) résout immédiatement (pas un signal de fin)
   - hypothèses partielles ET résultat final → événement 'partialResults'
   - début/fin de parole → événement 'listeningState' {status:'started'|'stopped'}
   - erreurs perdues en mode partialResults (reject après resolve ignoré)
     → un watchdog compense (onend synthétique après silence prolongé)
   ══════════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  // ── Détection Capacitor natif (no-op hors WebView Android) ──
  var _cap = (typeof window !== 'undefined') ? window.Capacitor : null;
  var _isNative = !!(_cap && typeof _cap.isNativePlatform === 'function' && _cap.isNativePlatform());
  if (!_isNative) return;

  var _SR = (_cap.Plugins && _cap.Plugins.SpeechRecognition) || null;

  console.log('[KA_NATIVE] Mode natif Android détecté — STT plugin :', _SR ? 'disponible' : 'ABSENT');

  /* ══════════════════════════════════════════════════════════════════════
     NativeSpeechRecognition — émulation Web Speech API
     ══════════════════════════════════════════════════════════════════════
     Interface compatible avec KA_STT (vital_ka_stt.js) et
     KA_CONVERSATION (vital_ka_conversation.js) :
       new Recog() ; .continuous .interimResults .lang .maxAlternatives
       .onresult(event{resultIndex, results[{isFinal, 0:{transcript}}]})
       .onerror({error}) ; .onend() ; .onspeechstart() ; .onspeechend()
       .start() .stop() .abort()

     Spécificités Android gérées ici :
     - Le plugin ne distingue pas partiel/final : on synthétise isFinal
       quand l'hypothèse est stable 1.4 s, et à la fin de session.
     - L'hypothèse est CUMULATIVE (phrase entière) : on émet seulement
       le segment non encore finalisé (préfixe suivi), comme Chrome.
     - Pas d'événement d'erreur en mode partialResults : watchdog 12 s.
     ══════════════════════════════════════════════════════════════════════ */
  function NativeSpeechRecognition() {
    // Propriétés Web Speech (assignées par le consommateur après new)
    this.continuous = true;
    this.interimResults = true;
    this.lang = 'fr-FR';
    this.maxAlternatives = 1;

    // Callbacks Web Speech
    this.onresult = null;
    this.onerror = null;
    this.onend = null;
    this.onaudiostart = null;
    this.onaudioend = null;
    this.onspeechstart = null;
    this.onspeechend = null;

    // État interne de session
    this._listening = false;
    this._stopping = false;      // stop()/abort() demandé par le consommateur
    this._finalizedPrefix = '';  // portion déjà émise en isFinal
    this._lastHyp = '';          // dernière hypothèse cumulative reçue
    this._stableTimer = null;    // finalisation sur hypothèse stable
    this._endTimer = null;       // clôture après listeningState 'stopped'
    this._watchdog = null;       // filet de sécurité (erreurs silencieuses)
    this._handles = [];          // listeners Capacitor à nettoyer
  }

  // ── Démarrage (async en interne ; exceptions synchrones style Web API) ──
  NativeSpeechRecognition.prototype.start = function () {
    if (this._listening) {
      var err = new Error('recognition has already started');
      err.name = 'InvalidStateError';
      throw err;
    }
    if (!_SR) {
      this._emitError('not-allowed');
      this._emitEnd();
      return;
    }
    this._resetSession();
    this._listening = true;
    this._startAsync();
  };

  NativeSpeechRecognition.prototype._startAsync = async function () {
    var self = this;
    try {
      // Permission micro (méthodes auto-générées par @CapacitorPlugin)
      try {
        var perm = await _SR.requestPermissions();
        if (perm && perm.speechRecognition && perm.speechRecognition !== 'granted') {
          self._listening = false;
          self._emitError('not-allowed');
          self._emitEnd();
          return;
        }
      } catch (ePerm) { /* version sans requestPermissions → tenter quand même */ }

      // Disponibilité du service de reconnaissance sur l'appareil
      try {
        var avail = await _SR.available();
        if (avail && avail.available === false) {
          self._listening = false;
          self._emitError('not-allowed');
          self._emitEnd();
          return;
        }
      } catch (eAvail) { /* ignorer — start() échouera le cas échéant */ }

      // Nettoyer d'éventuels listeners d'une session précédente
      await self._removeListeners();

      // Hypothèses partielles + résultat final (même événement côté plugin)
      var hPartial = await _SR.addListener('partialResults', function (data) {
        var text = (data && data.matches && data.matches.length) ? String(data.matches[0]) : '';
        if (text) self._onHypothesis(text);
      });
      self._handles.push(hPartial);

      // Début/fin de parole (barge-in + clôture de session)
      var hState = await _SR.addListener('listeningState', function (data) {
        if (!data) return;
        if (data.status === 'started') {
          self._armWatchdog();
          if (self.onspeechstart) self.onspeechstart(new Event('speechstart'));
        } else if (data.status === 'stopped') {
          self._scheduleSessionEnd();
        }
      });
      self._handles.push(hState);

      if (self.onaudiostart) self.onaudiostart(new Event('audiostart'));
      self._armWatchdog();

      // Résout immédiatement en mode partialResults ; reject = erreur précoce
      await _SR.start({
        language: self.lang || 'fr-FR',
        partialResults: true,
        popup: false,
        maxResults: self.maxAlternatives || 1,
      });
    } catch (e) {
      console.warn('[KA_NATIVE_SR] start() a échoué :', (e && e.message) || e);
      self._listening = false;
      self._emitError(self._mapError(e));
      self._emitEnd();
    }
  };

  // ── Arrêt : émet le segment final restant puis onend ──
  NativeSpeechRecognition.prototype.stop = function () {
    this._stopping = true;
    this._finalizeSegment();          // dernière portion parlée → isFinal
    this._teardown(false);
  };

  // ── Abandon : pas de résultat final ──
  NativeSpeechRecognition.prototype.abort = function () {
    this._stopping = true;
    this._teardown(true);
  };

  // ── Réception d'une hypothèse cumulative ──
  NativeSpeechRecognition.prototype._onHypothesis = function (text) {
    if (!this._listening) return;
    this._armWatchdog();
    if (text === this._lastHyp) return;
    this._lastHyp = text;

    // Fin de session déjà planifiée (parasite tardif) → annuler la clôture
    if (this._endTimer) { clearTimeout(this._endTimer); this._endTimer = null; }

    this._emitInterim();
    this._armStableTimer();
  };

  // Émet la portion non finalisée comme résultat intermédiaire
  NativeSpeechRecognition.prototype._emitInterim = function () {
    var segment = this._segment();
    if (!segment || !this.onresult) return;
    this.onresult({
      resultIndex: 0,
      results: [this._makeResult(segment, false)],
    });
  };

  // Segment courant = hypothèse cumulative moins le préfixe déjà finalisé
  NativeSpeechRecognition.prototype._segment = function () {
    var hyp = this._lastHyp || '';
    var pre = this._finalizedPrefix || '';
    if (pre && hyp.indexOf(pre) === 0) return hyp.slice(pre.length).trim();
    return hyp.trim();   // l'hypothèse a changé de formulation → reprendre entier
  };

  // Forme Web Speech : result[0].transcript + result.isFinal + result.length
  NativeSpeechRecognition.prototype._makeResult = function (transcript, isFinal) {
    var result = [{ transcript: transcript, confidence: isFinal ? 0.9 : 0.5 }];
    result.isFinal = isFinal;
    return result;
  };

  // Hypothèse stable depuis 1.4 s → finaliser le segment (comme Chrome)
  NativeSpeechRecognition.prototype._armStableTimer = function () {
    var self = this;
    if (this._stableTimer) clearTimeout(this._stableTimer);
    this._stableTimer = setTimeout(function () { self._finalizeSegment(); }, 1400);
  };

  NativeSpeechRecognition.prototype._finalizeSegment = function () {
    var segment = this._segment();
    if (!segment || !this._listening) return;
    this._finalizedPrefix = this._lastHyp;
    if (this.onresult) {
      this.onresult({
        resultIndex: 0,
        results: [this._makeResult(segment, true)],
      });
    }
  };

  // listeningState 'stopped' → laisser 900 ms au résultat final pour arriver
  NativeSpeechRecognition.prototype._scheduleSessionEnd = function () {
    var self = this;
    if (this._endTimer || this._stopping) return;
    this._endTimer = setTimeout(function () {
      self._endTimer = null;
      if (!self._listening) return;
      self._finalizeSegment();
      self._teardown(false);
    }, 900);
  };

  // Watchdog : en mode partialResults le plugin avale les erreurs.
  // Sans aucun événement pendant 12 s, on clôture (le consommateur relance).
  NativeSpeechRecognition.prototype._armWatchdog = function () {
    var self = this;
    if (this._watchdog) clearTimeout(this._watchdog);
    this._watchdog = setTimeout(function () {
      if (!self._listening) return;
      console.warn('[KA_NATIVE_SR] Watchdog — session muette, clôture.');
      self._finalizeSegment();
      self._teardown(false);
    }, 12000);
  };

  // Clôture propre : stop plugin, nettoyage, onspeechend + onend
  NativeSpeechRecognition.prototype._teardown = function (aborted) {
    if (this._stableTimer) { clearTimeout(this._stableTimer); this._stableTimer = null; }
    if (this._endTimer) { clearTimeout(this._endTimer); this._endTimer = null; }
    if (this._watchdog) { clearTimeout(this._watchdog); this._watchdog = null; }
    var wasListening = this._listening;
    this._listening = false;
    if (_SR && wasListening) {
      try { _SR.stop().catch(function () {}); } catch (e) { /* ignore */ }
    }
    this._removeListeners();
    if (!wasListening) return;
    if (this.onaudioend) this.onaudioend(new Event('audioend'));
    if (this.onspeechend) this.onspeechend(new Event('speechend'));
    this._emitEnd();
  };

  NativeSpeechRecognition.prototype._removeListeners = async function () {
    var hs = this._handles.splice(0);
    for (var i = 0; i < hs.length; i++) {
      try { await hs[i].remove(); } catch (e) { /* ignore */ }
    }
  };

  NativeSpeechRecognition.prototype._emitEnd = function () {
    if (this.onend) {
      var self = this;
      setTimeout(function () { if (self.onend) self.onend(new Event('end')); }, 0);
    }
  };

  NativeSpeechRecognition.prototype._emitError = function (code) {
    if (this.onerror) this.onerror({ error: code, message: code });
  };

  NativeSpeechRecognition.prototype._mapError = function (e) {
    var msg = String((e && e.message) || e || '');
    if (/permission|denied|not.allowed/i.test(msg)) return 'not-allowed';
    if (/no speech|no match|speech input/i.test(msg)) return 'no-speech';
    if (/network|server|busy/i.test(msg)) return 'network';
    return 'unknown';
  };

  NativeSpeechRecognition.prototype._resetSession = function () {
    this._stopping = false;
    this._finalizedPrefix = '';
    this._lastHyp = '';
    if (this._stableTimer) { clearTimeout(this._stableTimer); this._stableTimer = null; }
    if (this._endTimer) { clearTimeout(this._endTimer); this._endTimer = null; }
    if (this._watchdog) { clearTimeout(this._watchdog); this._watchdog = null; }
  };

  // ── Exposition globale (les modules STT la préfèrent à l'API web) ──
  window.KA_NATIVE_SR = NativeSpeechRecognition;
})();
