/* ══════════════════════════════════════════════════════════════════════════
   KA NATIVE — Pont Capacitor pour KA Phone
   ══════════════════════════════════════════════════════════════════════════
   Exposé uniquement dans la WebView Android (window.Capacitor présent).
   - window.SpeechRecognition : polyfill de la Web Speech API → plugin natif
     @capacitor-community/speech-recognition (Google SpeechRecognizer).
     KA utilise l'interface standard : new SR(), .lang/.continuous/.interimResults,
     .onresult (ev.results[i][0].transcript, isFinal), .onend, .onerror, .start()/.stop().
   - Flux natif (partialResults=true) : le canal « partialResults » livre les
     résultats intermédiaires PUIS le résultat final ; « listeningState » stopped
     signale la fin de l'écoute → on émet le résultat final (isFinal=true) + onend.
   - Sur le PC / navigateur, ce script ne fait rien (return immédiat).
   ══════════════════════════════════════════════════════════════════════════ */
(function () {
  if (typeof window.Capacitor === 'undefined') return;   // PC / PWA : rien à faire
  var Cap = window.Capacitor;
  var PLUGIN = 'SpeechRecognition';
  var plugin = (Cap.Plugins && Cap.Plugins.SpeechRecognition) || null;

  function call(method, opts) {
    if (plugin && typeof plugin[method] === 'function') {
      var r = plugin[method](opts || {});
      return (r && typeof r.then === 'function') ? r : Promise.resolve(r);
    }
    if (Cap.nativePromise) return Cap.nativePromise(PLUGIN, method, opts || {});
    return Promise.reject(new Error('Plugin SpeechRecognition indisponible'));
  }
  function listen(event, cb) {
    if (plugin && typeof plugin.addListener === 'function') return plugin.addListener(event, cb);
    if (Cap.addListener) return Cap.addListener(PLUGIN, event, cb);
    return Promise.resolve({ remove: function () {} });
  }

  function SR() {
    this.lang = 'fr-FR';
    this.continuous = false;
    this.interimResults = true;
    this.onstart = this.onresult = this.onerror = this.onend = null;
    this._running = false;
    this._handles = [];
    this._final = '';
  }
  SR.prototype._emit = function (h, ev) { try { if (h) h(ev); } catch (e) {} };
  SR.prototype._release = function () {
    this._running = false;
    this._handles.forEach(function (h) { try { h.remove(); } catch (e) {} });
    this._handles = [];
  };
  SR.prototype.start = function () {
    var self = this;
    if (self._running) return;
    self._running = true;
    self._final = '';
    call('requestPermissions').catch(function () { return null; })
      .then(function () {
        // Résultats intermédiaires + résultat final → onresult (isFinal=false d'abord)
        return listen('partialResults', function (data) {
          var matches = (data && data.matches) || [];
          if (!matches.length || !self._running) return;
          self._final = matches[matches.length - 1];
          self._emit(self.onresult, {
            resultIndex: 0,
            results: [[{ transcript: self._final }]]
          });
        }).then(function (h) { self._handles.push(h); });
      })
      .then(function () {
        // Fin de l'écoute → résultat final (isFinal=true) puis onend
        return listen('listeningState', function (data) {
          if (!self._running || !data || data.status !== 'stopped') return;
          self._release();
          if (self._final) {
            self._emit(self.onresult, {
              resultIndex: 0,
              results: [[{ transcript: self._final, isFinal: true }]]
            });
          }
          self._emit(self.onend);
        }).then(function (h) { self._handles.push(h); });
      })
      .then(function () {
        return call('start', { language: self.lang || 'fr-FR', partialResults: !!self.interimResults });
      })
      .then(function () { self._emit(self.onstart); })   // résolu au stop() natif ; onstart émis aussi là
      .catch(function (err) {
        self._release();
        self._emit(self.onerror, { error: 'not-allowed', message: String((err && err.message) || err) });
        self._emit(self.onend);
      });
  };
  SR.prototype.stop = function () {
    if (!this._running) return;
    call('stop').catch(function () {});
    this._release();
    this._emit(this.onend);
  };
  SR.prototype.abort = SR.prototype.stop;

  window.SpeechRecognition = SR;
  try { window.webkitSpeechRecognition = SR; } catch (e) {}
  if (window.console && console.log) console.log('KA · STT natif Android actif (plugin SpeechRecognition)');
})();
