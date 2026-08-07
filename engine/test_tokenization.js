/* ══════════════════════════════════════════════════════════════════════════
   TEST TOKENIZATION — Vérifie que toutes les conditions tokenisées
   (champ "tokens" dans les 8 JSON) sont valides et cohérentes :
   - tokens ∈ symptomMap
   - vecteurs non vides
   - aucune condition à seuils non tokenisée
   - aucun token absent de symptomMap
   ══════════════════════════════════════════════════════════════════════════ */
'use strict';

const fs = require('fs');
const path = require('path');

let passed = 0, failed = 0;
function ok(cond, label) {
  if (cond) { passed++; console.log('  ✅ ' + label); }
  else { failed++; console.log('  ❌ ' + label); }
}
function section(t) { console.log('\n══ ' + t + ' ══'); }

// ── Charge symptomMap de ka_core.js ──
const coreCode = fs.readFileSync(path.join(__dirname, 'ka_core.js'), 'utf8');
const smMatch = coreCode.match(/const symptomMap = \{([\s\S]*?)\n\};/);
const sm = {};
if (smMatch) {
  const lines = smMatch[1].split('\n');
  for (const line of lines) {
    const pairs = line.match(/"([^"]+)":"([^"]+)"/g);
    if (pairs) for (const p of pairs) { const m = p.match(/"([^"]+)":"([^"]+)"/); if (m) sm[m[1]] = m[2]; }
  }
}

const FILES = ['vital_ka_ntd.json', 'vital_ka_vih_tb.json', 'vital_ka_pediatrie.json',
  'vital_ka_urgences.json', 'vital_ka_sante_mentale.json', 'vital_ka_chroniques.json',
  'vital_ka_mere_enfant.json', 'vital_ka_malnutrition.json'];

const THRESHOLD_CONDITIONS = new Set([
  'hta','sam','mam','depistage_muac','pre_eclampsie','eclampsie','hemorragie_post_partum',
  'ictere_neonatal','prematurite','pneumonie_pcime','brulure','convulsion_febrile',
  'croissance_pcime','asthme_chronique','cpn1','asphyxie_neonatale'
]);
const PROTOCOL_CONDITIONS = new Set([
  'tarv_premiere_ligne','ptme','tb_traitement','tb_vih_coinfection','prophylaxie_prep',
  'contraception_post_partum','evaluation_trauma_abcde','vih_stade_oms'
]);

let totalTokenized = 0, totalTokens = 0, badTokens = 0;

for (const fname of FILES) {
  const d = JSON.parse(fs.readFileSync(path.join(__dirname, 'data', fname), 'utf8'));
  const coll = d.conditions || d.pathologies || {};
  section(fname.split('_').slice(-1)[0].replace('.json',''));
  for (const [key, cond] of Object.entries(coll)) {
    // Ignorer protocoles purs — normaux sans tokens
    if (PROTOCOL_CONDITIONS.has(key)) continue;

    if (THRESHOLD_CONDITIONS.has(key)) {
      // Condition à seuils : ne DOIT PAS avoir de tokens (serait trompeur)
      if (cond.tokens && cond.tokens.length > 0) {
        ok(false, key + ' : condition à seuils mais tokens présents (trompeur)');
      }
      continue;
    }

    if (!cond.tokens) {
      ok(false, key + ' : NI tokenisée NI à seuils NI protocole — oubli ?');
      continue;
    }

    totalTokenized++;
    totalTokens += cond.tokens.length;

    // Vérifier chaque token
    for (const t of cond.tokens) {
      if (!sm[t]) {
        ok(false, key + ' : token "' + t + '" absent du symptomMap');
        badTokens++;
      }
    }
  }
}

section('Bilan tokenisation');
ok(badTokens === 0, 'tous les tokens ∈ symptomMap (' + badTokens + ' erreurs)');
ok(totalTokenized >= 35, '≥ 35 conditions tokenisées (' + totalTokenized + ')');
ok(totalTokens >= 180, '≥ 180 tokens curés (' + totalTokens + ')');

// Vérifier que toutes les conditions tokenisées ont un vecteur non vide
// (stub encodeSympt via node)
globalThis.document = { getElementById(id) { return { value: '' }; } };
(0, eval)(coreCode + ';globalThis.encodeSympt=encodeSympt;globalThis.F=F;');
let emptyVectors = 0;
for (const fname of FILES) {
  const d = JSON.parse(fs.readFileSync(path.join(__dirname, 'data', fname), 'utf8'));
  const coll = d.conditions || d.pathologies || {};
  for (const [key, cond] of Object.entries(coll)) {
    if (PROTOCOL_CONDITIONS.has(key) || THRESHOLD_CONDITIONS.has(key)) continue;
    if (!cond.tokens) continue;
    const vec = encodeSympt(cond.tokens.join(' '));
    if (Object.keys(vec).length === 0) {
      console.log('  ⚠️  ' + key + ' : vecteur VIDE (tokens: ' + cond.tokens.join(', ') + ')');
      emptyVectors++;
    }
  }
}
ok(emptyVectors === 0, 'aucun vecteur vide (' + emptyVectors + ' problématiques)');

console.log('\n════════════════════════════════════════');
console.log('BILAN : ' + passed + ' ✅ / ' + failed + ' ❌ (' + (passed + failed) + ' assertions)');
console.log('Conditions tokenisées : ' + totalTokenized + ', tokens curés : ' + totalTokens);
process.exit(failed ? 1 : 0);
