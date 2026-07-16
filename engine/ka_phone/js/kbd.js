/**
 * KA Phone — Clavier AZERTY + Suggestions
 */

/* global K, KR, EM, SD, buildKbd, type, upd, renderSugs, sendMsg, API_URL, askKA */
'use strict';

const K = {txt:'',shift:false,lock:false,ts:0,alt:false,voice:false,vt:null,emo:false};
const KR = [
  [['1','~'],['2','@'],['3','#'],['4','$'],['5','%'],['6','^'],['7','&'],['8','*'],['9','('],['0',')']],
  [['a','à'],['z','æ'],['e','€'],['r','®'],['t','™'],['y','¥'],['u','ù'],['i','ï'],['o','œ'],['p','°']],
  [['q',''],['s','ß'],['d',''],['f',''],['g',''],['h',''],['j',''],['k',''],['l',''],['m','µ']],
  [['w',''],['x',''],['c','ç'],['v',''],['b',''],['n','ñ']]
];
const EM = ['😊','😂','❤️','🔥','✨','🙏','👍','🎉','😄','😍','🤔','😎','🥰','💪','🙌','👋','🎶','🌟','💡','🚀','🌍','🍕','☕','🎯','💬','✅','😘','🫶','🤩','😅','🫠','🤝','🌸','⭐','🎵'];
const SD = {
  '':['Sophie','Appeler','Réunion','Oui','Super','Merci','Demain'],
  'so':['Sophie','Soirée','Souvenir'],'ap':['Appeler','Appelle','Après'],
  'me':['Merci','Message','Même'],'ou':['Oui','Ouvert','Ouais'],
  'to':['Tokyo','Toi','Toujours'],'de':['Demain','Décision','Depuis'],
  're':['Réunion','Rendez-vous','Retrouve'],'su':['Super','Sur','Surtout'],
  'bi':['Bientôt','Bien','Bises'],'bo':['Bonjour','Bonsoir','Bon'],
  'co':['Comment','Comme','Contact'],'pr':['Prépare','Prendre','Prochain'],
  'pa':['Paris','Parfait','Partager'],'ma':['Maintenant','Matin','Mais'],
  'vo':['Voici','Voilà','Voyage'],'sa':['Salut','Samedi','Sans'],
  'tr':['Très','Travail','Trouver']
};

function mk(lbl, alt, w, cls, fn) {
  const el = document.createElement('div');
  el.className = 'key' + (cls ? ' ' + cls : '');
  el.style.width = w + 'px';
  el.setAttribute('role','button');
  el.innerHTML = '<span class="key__c">' + lbl + '</span>' + (alt ? '<span class="key__a">' + alt + '</span>' : '');
  el.addEventListener('pointerdown', function(e) {
    e.preventDefault(); el.classList.add('key--p');
    setTimeout(function() { el.classList.remove('key--p'); }, 115); fn();
  });
  return el;
}

function buildKbd() {
  const rn = document.getElementById('rn'); rn.innerHTML = '';
  KR[0].forEach(function(c) { rn.appendChild(mk(K.alt ? (c[1]||c[0]) : c[0], K.alt ? c[0] : c[1], 32, '', function() { type(K.alt ? (c[1]||c[0]) : c[0]); })); });
  ['r1','r2'].forEach(function(id, ri) {
    const r = document.getElementById(id); r.innerHTML = '';
    KR[ri+1].forEach(function(c) {
      const d = (K.shift||K.lock) ? c[0].toUpperCase() : c[0];
      r.appendChild(mk(d, c[1], 33, '', function() { type(d); if (K.shift&&!K.lock) { K.shift=false; buildKbd(); } }));
    });
  });
  const r3 = document.getElementById('r3'); r3.innerHTML = '';
  r3.appendChild(mk(K.lock?'⇪':'⇧','',43,'key--sp'+((K.shift||K.lock)?' key--sft':''), function() {
    const n = Date.now();
    if (n - K.ts < 280) { K.lock = !K.lock; K.shift = K.lock; }
    else { K.shift = !K.shift; K.lock = false; }
    K.ts = n; buildKbd();
  }));
  KR[3].forEach(function(c) {
    const d = (K.shift||K.lock) ? c[0].toUpperCase() : c[0];
    r3.appendChild(mk(d, c[1], 35, '', function() { type(d); if (K.shift&&!K.lock) { K.shift=false; buildKbd(); } }));
  });
  r3.appendChild(mk('⌫','',43,'key--sp key--del', function() { K.txt = K.txt.slice(0,-1); upd(); }));
  const rs = document.getElementById('rs'); rs.innerHTML = '';
  rs.appendChild(mk(K.alt?'ABC':'123','',49,'key--sp', function() { K.alt=!K.alt; buildKbd(); }));
  const sp = document.createElement('div'); sp.className = 'key key--spc'; sp.style.flex = '1';
  sp.innerHTML = '<span class="key__c">espace</span>';
  sp.addEventListener('pointerdown', function(e) { e.preventDefault(); sp.classList.add('key--p'); setTimeout(function() { sp.classList.remove('key--p'); }, 115); type(' '); });
  rs.appendChild(sp);
  rs.appendChild(mk('Envoyer','',82,'key--life', function() { sendMsg(); }));
}

function type(c) { K.txt += c; upd(); }
function upd() { document.getElementById('ftxt').textContent = K.txt; document.getElementById('sbtn').classList.toggle('ib__snd--on', K.txt.length > 0); renderSugs(); }

function getSugs(t) {
  const l = (t.trim().split(' ').pop()||'').toLowerCase();
  for (const k of Object.keys(SD)) { if (k && l.startsWith(k)) return SD[k].slice(0,6); }
  return SD[''].slice(0,6);
}

function renderSugs() {
  const c = document.getElementById('sgs'); c.innerHTML = '';
  getSugs(K.txt).forEach(function(w, i) {
    const d = document.createElement('div');
    d.className = 'sg' + (i===0?' sg--h':'');
    d.setAttribute('role','option'); d.textContent = w;
    d.addEventListener('pointerdown', function(e) {
      e.preventDefault();
      const p = K.txt.trim().split(' ');
      p[p.length-1] = w;
      K.txt = p.join(' ') + ' ';
      upd();
    });
    c.appendChild(d);
  });
}

function paste() {
  const w = ['Sophie','Réunion demain ?','Ok pour 19h !','Super idée !'];
  K.txt += w[Math.floor(Math.random()*w.length)];
  upd();
}

function sendMsg() {
  const val = K.txt.trim(); if (!val) return;
  const c = document.getElementById('msglist');
  const m = document.createElement('div'); m.className = 'msg msg--m'; m.textContent = val;
  c.appendChild(m); c.scrollTop = c.scrollHeight;
  K.txt = ''; upd();
  const think = document.createElement('div'); think.className = 'msg msg--t'; think.style.opacity = '0.6';
  think.innerHTML = '<span style="animation:pulse 1.2s ease-in-out infinite">●</span> KA réfléchit…';
  think.id = 'ka-thinking'; c.appendChild(think); c.scrollTop = c.scrollHeight;
  askKA(val).then(function(reply) {
    const t = document.getElementById('ka-thinking');
    if (t) t.remove();
    const r = document.createElement('div'); r.className = 'msg msg--t'; r.textContent = reply;
    c.appendChild(r); c.scrollTop = c.scrollHeight;
  });
}

function toggleVoice() {
  K.voice = !K.voice;
  const btn = document.getElementById('tbv'), lbl = document.getElementById('vl');
  btn.classList.toggle('tbn--on', K.voice);
  btn.setAttribute('aria-pressed', K.voice);
  if (K.voice) {
    lbl.textContent = '● Écoute…';
    // Vraie reconnaissance vocale via Web Speech API
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SR) {
      K.rec = new SR();
      K.rec.lang = 'fr-FR'; K.rec.continuous = false; K.rec.interimResults = true;
      K.rec.onresult = function(ev) {
        var txt = '';
        for (var i = ev.resultIndex; i < ev.results.length; i++) { txt += ev.results[i][0].transcript; }
        K.txt = txt; upd();
      };
      K.rec.onend = function() {
        if (K.voice) {
          try { K.rec.start(); } catch(e) {
            K.voice = false; btn.classList.remove('tbn--on'); lbl.textContent = 'Voix'; btn.setAttribute('aria-pressed','false');
          }
        }
      };
      K.rec.onerror = function() { K.voice = false; btn.classList.remove('tbn--on'); lbl.textContent = 'Voix'; btn.setAttribute('aria-pressed','false'); };
      try { K.rec.start(); } catch(e) {}
    } else {
      // Fallback simulation
      lbl.textContent = 'Voix (simulé)';
      var phrases = ['Rendez-vous demain à 19h ?','Appelle Sophie','Prépare ma réunion'];
      var phrase = phrases[Math.floor(Math.random()*phrases.length)];
      var i = 0;
      K.vt = setInterval(function() {
        if (!K.voice || i >= phrase.length) { clearInterval(K.vt); if (K.voice) { K.voice = false; btn.classList.remove('tbn--on'); lbl.textContent = 'Voix'; btn.setAttribute('aria-pressed','false'); } return; }
        K.txt += phrase[i++]; upd();
      }, 72);
    }
  } else {
    if (K.rec) { try { K.rec.stop(); } catch(e) {} }
    clearInterval(K.vt); lbl.textContent = 'Voix';
  }
}

function toggleEmoji() {
  K.emo = !K.emo;
  const ep = document.getElementById('ep'), kd = document.getElementById('kbd'), btn = document.getElementById('tbe');
  btn.classList.toggle('tbn--on', K.emo); btn.setAttribute('aria-pressed', K.emo);
  if (K.emo) {
    ep.innerHTML = '';
    EM.forEach(function(e) {
      const b = document.createElement('div'); b.className = 'eb'; b.setAttribute('role','button'); b.textContent = e;
      b.addEventListener('pointerdown', function(ev) { ev.preventDefault(); type(e); });
      ep.appendChild(b);
    });
    ep.classList.add('ep--on'); kd.style.display = 'none';
  } else { ep.classList.remove('ep--on'); kd.style.display = 'block'; }
}

buildKbd(); renderSugs();
