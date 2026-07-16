/**
 * KA Phone — Call Screen
 * ================
 * Appel vocal avec TTS (synthèse) + STT (reconnaissance) réels.
 */
/* global callSecs, callIv, callTTS, askKA */

let callSecs = 0, callIv = null, callTTS = null;

function startCall() {
  callSecs = 0; clearInterval(callIv);
  callIv = setInterval(function() {
    callSecs++;
    var m = String(Math.floor(callSecs/60)).padStart(2,'0'), s = String(callSecs%60).padStart(2,'0');
    var el = document.getElementById('ctmr');
    if (el) el.textContent = m + ':' + s;
  }, 1000);
  var w = document.getElementById('cwv');
  if (!w) return;
  w.innerHTML = '';
  for (var i = 0; i < 22; i++) {
    var b = document.createElement('div');
    b.className = 'wb';
    b.style.cssText = '--wh:' + (3+Math.random()*22) + 'px;animation-duration:' + (0.35+Math.random()*0.5) + 's;animation-delay:' + (Math.random()*0.4) + 's';
    w.appendChild(b);
  }
  // KA parle après 2 secondes
  setTimeout(function() {
    if (typeof cur !== 'undefined' && cur !== 's-call') return;
    kaCallSpeak('Bonjour, je suis KA. Comment puis-je vous aider ?');
  }, 2000);
}

function stopCall() {
  clearInterval(callIv);
  if (callTTS) { callTTS.cancel(); callTTS = null; }
  if (window._callRec) { try { window._callRec.stop(); } catch(e) {} }
}

// Synthèse vocale (TTS)
function kaCallSpeak(text) {
  if (!('speechSynthesis' in window)) return;
  if (callTTS) callTTS.cancel();
  callTTS = new SpeechSynthesisUtterance(text);
  callTTS.lang = 'fr-FR'; callTTS.rate = 1.0; callTTS.pitch = 1.05;
  var voices = speechSynthesis.getVoices();
  for (var i = 0; i < voices.length; i++) {
    if (voices[i].lang.indexOf('fr') >= 0) { callTTS.voice = voices[i]; break; }
  }
  speechSynthesis.speak(callTTS);
}

// Reconnaissance vocale pendant l'appel
function kaCallListen() {
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { alert('Reconnaissance vocale non disponible'); return; }
  var rec = new SR();
  rec.lang = 'fr-FR'; rec.continuous = false; rec.interimResults = true;
  var tr = document.getElementById('call-transcript');
  if (tr) tr.textContent = '● Écoute…';
  rec.onresult = function(ev) {
    var txt = '';
    for (var i = ev.resultIndex; i < ev.results.length; i++) { txt += ev.results[i][0].transcript; }
    if (tr) tr.textContent = '"' + txt + '"';
    if (ev.results[ev.results.length-1].isFinal) {
      if (typeof askKA === 'function') {
        askKA(txt).then(function(reply) {
          if (tr) tr.textContent = reply.slice(0, 80);
          kaCallSpeak(reply);
        });
      }
    }
  };
  rec.onerror = function() { if (tr) tr.textContent = ''; };
  rec.onend = function() { if (tr && tr.textContent.indexOf('Écoute') >= 0) tr.textContent = ''; };
  window._callRec = rec;
  try { rec.start(); } catch(e) {}
}

function buildCapWave() {
  var w = document.getElementById('capwv');
  if (!w) return;
  w.innerHTML = '';
  for (var i = 0; i < 18; i++) {
    var b = document.createElement('div');
    b.style.cssText = 'width:2.5px;border-radius:2px;background:rgba(61,219,160,.6);--wh:' + (3+Math.random()*16) + 'px;animation:wave ' + (0.35+Math.random()*0.5) + 's ease-in-out infinite alternate ' + (Math.random()*0.4) + 's';
    w.appendChild(b);
  }
}
