/* ══════════════════════════════════════════════════════════════════════════
   TEST MOTEUR DE RÈGLES DE SEUILS
   Vérifie : SAM (MUAC), HTA (TA), Pneumonie PCIME (FR), fallback,
   non-régression des suites existantes.
   ══════════════════════════════════════════════════════════════════════════ */
'use strict';
const fs = require('fs'), path = require('path');

let passed = 0, failed = 0;
function ok(cond, label) { if (cond) { passed++; console.log('  ✅ ' + label); } else { failed++; console.log('  ❌ ' + label); } }

// ── Stubs ──
const ALL_JSON = ['vital_ka_diseases.json','vital_ka_malaria.json','vital_ka_tropical.json',
  'vital_ka_ntd.json','vital_ka_vih_tb.json','vital_ka_chroniques.json','vital_ka_pediatrie.json',
  'vital_ka_urgences.json','vital_ka_mere_enfant.json','vital_ka_malnutrition.json','vital_ka_sante_mentale.json'];

function setVitals(vals) {
  globalThis.document = { getElementById(id) { return { value: vals[id] !== undefined ? String(vals[id]) : '' }; } };
}

globalThis.window = {};
globalThis.document = { getElementById: () => ({ value: '' }) };  // requis AVANT chargement (encodeSympt lit le DOM)
globalThis.fetch = async (url) => {
  const name = String(url).split('/').pop();
  const f = ALL_JSON.find(x => x === name);
  if (!f) throw new Error('fetch 404: ' + url);
  return { ok: true, status: 200, json: async () => JSON.parse(fs.readFileSync(path.join(__dirname, 'data', f), 'utf8')) };
};

const code = fs.readFileSync(path.join(__dirname, 'ka_core.js'), 'utf8');
(0, eval)(code + ';globalThis.DB=DB;globalThis.ensureDB=ensureDB;globalThis.getDB=getDB;globalThis.F=F;globalThis.evaluateRules=evaluateRules;globalThis.readPatientData=readPatientData;globalThis.encodeSympt=encodeSympt;globalThis.cosineSim=cosineSim;globalThis.getVector=getVector;');

(async () => {
  await ensureDB();
  const db = getDB();
  ok(db['sam'] && db['sam'].seuils, 'SAM a des seuils definis');
  ok(db['hta'] && db['hta'].seuils, 'HTA a des seuils definis');
  ok(db['pneumonie_pcime'] && db['pneumonie_pcime'].seuils, 'Pneumonie PCIME a des seuils');

  /* ═══ SAM (MUAC=110, age 24mo, oedeme+fonte) ═══ */
  setVitals({ patientAge: '2', vitalMuac: '110' });
  let pt = readPatientData([]);
  pt.symptoms = ['œdèmes_bilatéraux', 'fonte_musculaire'];
  pt.age_months = 24;
  let rs = evaluateRules(pt, db);
  ok(rs['sam'] && rs['sam'] >= 0.9, 'SAM detecte (MUAC=110<115, 6-59mo, oedeme+fonte = ' + (rs['sam'] || 0).toFixed(2) + ')');

  /* ═══ MAM (MUAC=120, age 18mo) ═══ */
  setVitals({ patientAge: '1', vitalMuac: '120' });
  pt = readPatientData([]);
  pt.age_months = 18;
  rs = evaluateRules(pt, db);
  ok(rs['mam'] && rs['mam'] >= 0.70, 'MAM detecte (MUAC=120, 115-124mm = ' + (rs['mam'] || 0).toFixed(2) + ')');

  /* ═══ HTA (TA=150/95, age 55) ═══ */
  setVitals({ patientAge: '55', patientGender: 'homme', vitalTASyst: '150', vitalTADiast: '95' });
  pt = readPatientData(['céphalées']);
  rs = evaluateRules(pt, db);
  ok(rs['hta'] && rs['hta'] >= 0.8, 'HTA detecte (TA=150/95 = ' + (rs['hta'] || 0).toFixed(2) + ')');

  /* ═══ HTA severe (TA=185) sans diastolique ═══ */
  setVitals({ patientAge: '60', vitalTASyst: '185' });
  pt = readPatientData([]);
  rs = evaluateRules(pt, db);
  ok(rs['hta'] && rs['hta'] >= 0.9, 'HTA severe (TA=185, TAS>=180 = ' + (rs['hta'] || 0).toFixed(2) + ')');

  /* ═══ HTA symptomes sans TA (fallback symbolique) ═══ */
  setVitals({ patientAge: '45', patientGender: 'femme' });
  pt = readPatientData(['céphalées', 'vertiges']);
  rs = evaluateRules(pt, db);
  ok(rs['hta'] && rs['hta'] >= 0.65, 'HTA fallback symptomes (maux de tete+vertiges = ' + (rs['hta'] || 0).toFixed(2) + ')');

  /* ═══ Pneumonie PCIME (FR=52, age 6mo, toux) ═══ */
  setVitals({ patientAge: '0', vitalFR: '52' });
  pt = readPatientData(['toux_grasse']);
  pt.age_months = 6;
  rs = evaluateRules(pt, db);
  ok(rs['pneumonie_pcime'] && rs['pneumonie_pcime'] >= 0.8, 'Pneumonie PCIME (FR=52>=50, 2-11mo, toux = ' + (rs['pneumonie_pcime'] || 0).toFixed(2) + ')');

  /* ═══ Pneumonie PCIME symbolique (pas de FR) ═══ */
  setVitals({ patientAge: '1' });
  pt = readPatientData(['respiration_rapide', 'tirage', 'stridor']);
  pt.age_months = 12;
  rs = evaluateRules(pt, db);
  ok(rs['pneumonie_pcime'] && rs['pneumonie_pcime'] >= 0.7, 'Pneumonie PCIME symbolique (respiration+tirage+stridor = ' + (rs['pneumonie_pcime'] || 0).toFixed(2) + ')');

  /* ═══ Pre-eclampsie (symptomes sans TA) ═══ */
  setVitals({ patientAge: '28', patientGender: 'femme' });
  pt = readPatientData(['céphalées', 'œdème_membre', 'troubles_vision']);
  rs = evaluateRules(pt, db);
  ok(rs['pre_eclampsie'] && rs['pre_eclampsie'] >= 0.8, 'Pre-eclampsie symptomes (cephal+oedeme+vision = ' + (rs['pre_eclampsie'] || 0).toFixed(2) + ')');

  /* ═══ Eclampsie (convulsions+coma) ═══ */
  setVitals({ patientAge: '25', patientGender: 'femme' });
  pt = readPatientData(['convulsions_tonico_cloniques', 'coma']);
  rs = evaluateRules(pt, db);
  ok(rs['eclampsie'] && rs['eclampsie'] >= 0.9, 'Eclampsie (convulsions+coma = ' + (rs['eclampsie'] || 0).toFixed(2) + ')');

  /* ═══ Sans aucun input vital (fallback sain) ═══ */
  setVitals({ patientAge: '35', patientGender: 'homme' });
  pt = readPatientData([]);
  rs = evaluateRules(pt, db);
  ok(Object.keys(rs).length === 0, 'Sans signes vitaux: 0 seuil declenche (' + Object.keys(rs).length + ')');

  console.log('\n════════════════════════════════════════');
  console.log('BILAN SEUILS : ' + passed + ' ✅ / ' + failed + ' ❌ (' + (passed + failed) + ' assertions)');
  if (failed) process.exit(1);
})();
