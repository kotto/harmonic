/* test_askka_flow.js — SIMULATION DU FLUX askKA (ka_index.html)
   ==============================================================
   Reproduit exactement la logique de askKA branchée dans l'app :
   1. KAHybrid.repondre(message) → phraseModele (instantané, garanti)
   2. REFUS → FINAL (plus d'escalade : le cerveau hallucine parfois —
      « météo à Paris » → « Art nouveau… » — on refuse plutôt qu'inventer)
   3. Secours sans noyau : /api/chat, refus honnête si hors-ligne

   Usage : node test_askka_flow.js
*/
'use strict';

var fs = require('fs');
var path = require('path');

// ── Shim navigateur minimal (comme la WebView) ──
global.window = global;
var store = {};
global.localStorage = {
  getItem: function (k) { return k in store ? store[k] : null; },
  setItem: function (k, v) { store[k] = String(v); }
};
global.location = { hostname: '127.0.0.1' };
global.AbortSignal = global.AbortSignal || { timeout: function () { return null; } };

// fetch réel → le serveur KA local (pour le chemin de secours)
var API_URL = 'http://127.0.0.1:8765';
var API_ONLINE = true;

// ── Le noyau hybride (exactement celui de l'app) ──
require(path.join(__dirname, 'ka-mobile-android', 'www', 'ka_hybrid.js'));
var KAHybrid = global.KAHybrid;

// ── askKA — copie conforme de ka_index.html (version FINALE) ──
async function repondreCerveau(message) {
  try {
    var uid = store['ka_user_id'] || ('user_' + Date.now().toString(36));
    store['ka_user_id'] = uid;
    var hist = [];
    try { hist = JSON.parse(store['ka_chat_hist'] || '[]'); } catch (e) {}
    hist = hist.slice(-6);
    var res = await fetch(API_URL + '/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: message, user_id: uid, history: hist })
    });
    if (!res.ok) throw new Error('API error');
    var data = await res.json();
    hist.push({ role: 'user', content: message });
    hist.push({ role: 'assistant', content: (data.response || '').slice(0, 500) });
    store['ka_chat_hist'] = JSON.stringify(hist.slice(-6));
    return data.response || '';
  } catch (e) {
    API_ONLINE = false;
    return '';
  }
}

async function askKA(message) {
  if (window.KAHybrid) {
    var core = KAHybrid.repondre(message);
    return KAHybrid.phraseModele(core);
  }
  if (!API_ONLINE) return 'Je ne peux pas répondre à ça — ce n\'est pas dans ce que je connais.';
  var rep = await repondreCerveau(message);
  return rep || 'Je ne peux pas répondre à ça — ce n\'est pas dans ce que je connais.';
}

// ── Le protocole : noyau garantit / hors-domaine → refus honnête ──
var CAS = [
  // (question, attendu-dans-la-réponse | 'REFUS' = refus honnête attendu)
  ["7 × 8", "56"],
  ["c'est quoi le diabète ?", "glycémie"],
  ["que faire en cas d'avc ?", "15"],
  ["qui es-tu ?", "KA"],
  ["-12 × -2", "24"],
  ["0,1 × 0,1", "0.01"],
  ["8x8", "64"],
  ["quel est le plus long fleuve d'Afrique ?", "REFUS"],
  ["what is 7 + 8 ?", "REFUS"],
  ["raconte une blague", "REFUS"],
  ["quasar", "REFUS"],
  ["quelle est la météo à Paris ?", "REFUS"],
  ["qui a gagné le match hier ?", "REFUS"],
];

(async function () {
  console.log('═'.repeat(66));
  console.log('SIMULATION DU FLUX askKA — noyau seul, refus final (sans réseau)');
  console.log('═'.repeat(66));
  var ok = 0;
  var offline = [];
  for (var i = 0; i < CAS.length; i++) {
    var q = CAS[i][0], attendu = CAS[i][1];
    var t0 = Date.now();
    var rep = await askKA(q);
    var dt = Date.now() - t0;
    var source = KAHybrid.repondre(q).type;
    var passe;
    if (attendu === 'REFUS') {
      passe = rep.indexOf('ne peux pas répondre') >= 0;
    } else {
      passe = rep.indexOf(attendu) >= 0;
    }
    if (passe) ok++;
    console.log((passe ? '✅' : '❌') + ' [' + source + '] « ' + q + ' » (' + dt + ' ms)');
    console.log('      → ' + rep.slice(0, 100).replace(/\n/g, ' '));
    if (passe && dt > 5) offline.push(q); // le noyau doit être instantané
  }
  console.log('\nRÉSULTAT : ' + ok + '/' + CAS.length + (ok === CAS.length ? '  ✅' : '  ❌'));
  if (offline.length) console.log('⚠️  réponses >5 ms (le noyau devrait être instantané) : ' + offline.join(', '));
  process.exit(ok === CAS.length ? 0 : 1);
})();
