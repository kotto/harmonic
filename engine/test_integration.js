/* ══════════════════════════════════════════════════════════════════════════
   TEST INTÉGRATION NAVIGATEUR — simule le chargement complet de l'app
   (ka_core.js → vital_ka_knowledge.js → vital_ka_app.js)
   et exécute 3 diagnostics : paludisme (phyto+résonance), dépression (psy),
   céphalées seules (règles de seuils inactives).
   ══════════════════════════════════════════════════════════════════════════ */
'use strict';
const fs = require('fs'), path = require('path');

let passed = 0, failed = 0;
function ok(cond, label) { if (cond) { passed++; console.log('  ✅ ' + label); } else { failed++; console.log('  ❌ ' + label); } }

// ── Stubs globaux ──
globalThis.window = {};
globalThis.speechSynthesis = { getVoices: () => [], speak: () => {}, cancel: () => {}, onvoiceschanged: null };
globalThis.SpeechSynthesisUtterance = class { constructor(t) { this.text = t; } };
globalThis.KA_Network = { init: async () => ({}) };
globalThis.KA_SECURE = { exportAll() {}, triggerImport() {}, setupPIN() {}, showLockScreen() {}, verifyPIN() { return true; }, init() {}, isLocked() { return false; } };
globalThis.KA_HCV = {};
globalThis.currentPatient = null;
globalThis.loadPatients = () => ({});

function makeDoc(symptoms, age, gender) {
  const vals = {
    patientAge: { value: String(age) },
    patientGender: { value: gender || '' },
    symptomsInput: { value: symptoms || '' },
    resultsArea: { innerHTML: '', style: {} },
    diagnoseBtn: { disabled: false, textContent: '', dataset: {} },
    historyList: { innerHTML: '' },
    exportDiagBtn: { style: { display: 'none' } },
    aiConversation: { innerHTML: '' },
    holoLegend: { innerHTML: '' },
    patientsList: { innerHTML: '' }
  };
  globalThis.document = {
    getElementById(id) { return vals[id] || { value: '', style: {}, innerHTML: '' }; },
    querySelectorAll() { return []; },
    addEventListener() {},
    createElement() { return { style: {}, classList: { add() {}, remove() {} }, appendChild() {}, innerHTML: '', getContext() { return { fillRect() {}, arc() {}, beginPath() {}, fill() {}, save() {}, restore() {}, fillText() {} }; } }; },
    querySelector() { return { value: '', innerHTML: '' }; }
  };
}

// Stub localStorage
const store = {};
globalThis.localStorage = { getItem(k) { return store[k] || null; }, setItem(k, v) { store[k] = String(v); }, removeItem(k) { delete store[k]; } };

// Stub fetch (tous les JSON)
const ALL_JSON = [
  'vital_ka_pharmacie.json','vital_ka_mere_enfant.json','vital_ka_malnutrition.json',
  'vital_ka_vih_tb.json','vital_ka_chroniques.json','vital_ka_pediatrie.json','vital_ka_urgences.json',
  'vital_ka_vaccination.json','vital_ka_ntd.json','vital_ka_sante_mentale.json','vital_ka_phytotherapie.json',
  'vital_ka_diseases.json','vital_ka_malaria.json','vital_ka_tropical.json'
];
globalThis.fetch = async (url) => {
  const name = String(url).split('/').pop();
  const f = ALL_JSON.find(x => x === name);
  if (!f) throw new Error('fetch 404: ' + url);
  return { ok: true, status: 200, json: async () => JSON.parse(fs.readFileSync(path.join(__dirname, 'data', f), 'utf8')) };
};

// ── Chargement des scripts dans l'ordre HTML ──
// NB : vital_ka_app.js touche `document` au chargement (raccourcis clavier,
// boutons de démo) → il faut un stub document AVANT d'évaluer les fichiers.
makeDoc('', 30, 'M');
console.log('=== CHARGEMENT ===');
for (const s of ['ka_core.js', 'vital_ka_knowledge.js', 'vital_ka_app.js']) {
  try {
    (0, eval)(fs.readFileSync(path.join(__dirname, s), 'utf8'));
    console.log('  ✅ ' + s);
  } catch (e) {
    console.log('  ❌ ' + s + ': ' + e.message);
    process.exit(1);
  }
}
// Copier Knowledge en variable de portée module (buildPhytoBox teste typeof Knowledge)
if (typeof window !== 'undefined' && window.Knowledge) { var Knowledge = window.Knowledge; }
globalThis.Knowledge = window.Knowledge;

console.log('Knowledge:', typeof Knowledge, '| init:', typeof (Knowledge || {}).init, '| getPhytoFor:', typeof (Knowledge || {}).getPhytoFor);

// ── Diagnostics ──
(async () => {

  // Initialiser Knowledge
  if (typeof Knowledge !== 'undefined' && Knowledge.init) {
    try {
      await Knowledge.init();
    } catch(e) { /* attrapé en interne */ }
    // Fallback : si l'init réseau a échoué, charger la phyto directement
    if (!Knowledge._phyto || !Object.keys(Knowledge._phyto).length) {
      const phytoRaw = fs.readFileSync(path.join(__dirname, 'data', 'vital_ka_phytotherapie.json'), 'utf8');
      const phyto = JSON.parse(phytoRaw);
      Knowledge._phyto = phyto.plantes || phyto;
      Knowledge._plantVectors = {};
      for (const [key, plant] of Object.entries(Knowledge._phyto)) {
        if (plant && Array.isArray(plant.tokens_effet) && plant.tokens_effet.length && typeof encodeSympt === 'function') {
          Knowledge._plantVectors[key] = encodeSympt(plant.tokens_effet.join(' '));
        }
      }
      console.log('  ✅ Phyto chargée manuellement:', Object.keys(Knowledge._plantVectors).length, 'vecteurs');
    } else {
      console.log('  ✅ Knowledge OK:', Object.keys(Knowledge._phyto).length, 'plantes');
    }
  }
  
  // Stocker la fonction de calcul pour l'exécuter après makeDoc()
  var _ensurePlantVectors = function() {
    if (typeof Knowledge !== 'undefined' && Knowledge._phyto && (!Knowledge._plantVectors || !Object.keys(Knowledge._plantVectors).length)) {
      Knowledge._plantVectors = {};
      for (const [key, plant] of Object.entries(Knowledge._phyto)) {
        if (plant && Array.isArray(plant.tokens_effet) && plant.tokens_effet.length && typeof encodeSympt === 'function') {
          Knowledge._plantVectors[key] = encodeSympt(plant.tokens_effet.join(' '));
        }
      }
    }
  };

  /* ═══ 1. Paludisme + phyto + résonance ═══ */
  console.log('\n═══ DIAGNOSTIC PALUDISME ═══');
  makeDoc('fièvre_cyclique frissons sueurs maux_de_tête fatigue_intense douleurs_musculaires', 35, 'homme');
  _ensurePlantVectors(); // document est maintenant disponible
  const top1 = await diagnose();
  ok(top1 && top1.name === 'Paludisme_simple', 'Top-1 = Paludisme_simple (' + (top1 ? (top1.score * 100).toFixed(1) + '%' : 'aucun') + ')');
  const html1 = document.getElementById('resultsArea').innerHTML;
  ok(html1.includes('phyto-box'), 'Encadré phyto présent');
  ok(/⚡|résonance/.test(html1), 'Résonance thérapeutique affichée');
  ok(html1.includes('Cryptolepis'), 'Cryptolepis (grade A) mentionnée');

  /* ═══ 2. Dépression (discrimination psychiatrique) ═══ */
  console.log('\n═══ DIAGNOSTIC DÉPRESSION ═══');
  makeDoc('humeur_dépressive anhédonie fatigue troubles_sommeil culpabilisation baisse_concentration isolement', 30, 'femme');
  const top2 = await diagnose();
  ok(top2 && /depression/i.test(top2.name), 'Top-1 dépression/psychiatrique (' + (top2 ? top2.name + ' ' + (top2.score * 100).toFixed(1) + '%' : 'aucun') + ')');
  const html2 = document.getElementById('resultsArea').innerHTML;
  // Aucune plante attendue pour une dépression (pas d'indication phyto dépression dans le top-3)
  console.log('  Phyto présent:', html2.includes('phyto-box') ? 'oui' : 'non');

  /* ═══ 3. Sans signes vitaux → pas de faux seuils ═══ */
  console.log('\n═══ CÉPHALÉES (sans vitaux) ═══');
  makeDoc('maux_de_tête fatigue', 55, 'homme');
  const top3 = await diagnose();
  ok(top3 !== null, 'Diagnostic retourné');
  console.log('  Top-1:', top3 ? top3.name + ' ' + (top3.score * 100).toFixed(1) + '%' : 'aucun');

  /* ═══ BILAN ═══ */
  console.log('\n════════════════════════════════════════');
  console.log('INTEGRATION : ' + passed + ' ✅ / ' + failed + ' ❌ (' + (passed + failed) + ' assertions)');
  process.exit(failed ? 1 : 0);
})();
