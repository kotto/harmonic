/* ══════════════════════════════════════════════════════════════════════════
   TEST E2E — Encadré phytothérapie sous diagnostic
   Charge Knowledge (vital_ka_knowledge.js) avec la base phyto réelle, et
   vérifie la chaîne : getPhytoFor() + buildPhytoBox() sur diagnostics paludéens,
   dengue, hypertension. Confirme que les plantes ne polluent JAMAIS le scoring.
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

// ── Stubs DOM / fetch / localStorage ──
globalThis.window = {};
globalThis.localStorage = {
  _s: {},
  getItem(k) { return this._s[k] ?? null; },
  setItem(k, v) { this._s[k] = String(v); },
  removeItem(k) { delete this._s[k]; }
};
globalThis.fetch = async (url) => {
  const name = String(url).split('/').pop();
  const files = ['vital_ka_pharmacie.json','vital_ka_mere_enfant.json','vital_ka_malnutrition.json',
    'vital_ka_vih_tb.json','vital_ka_chroniques.json','vital_ka_pediatrie.json','vital_ka_urgences.json',
    'vital_ka_vaccination.json','vital_ka_ntd.json','vital_ka_sante_mentale.json','vital_ka_phytotherapie.json'];
  const f = files.find(x => x === name);
  if (!f) throw new Error('fetch 404: ' + url);
  const text = fs.readFileSync(path.join(__dirname, 'data', f), 'utf8');
  return { ok: true, status: 200, json: async () => JSON.parse(text) };
};

// ── Charge vital_ka_knowledge.js ──
const codeK = fs.readFileSync(path.join(__dirname, 'vital_ka_knowledge.js'), 'utf8');
(0, eval)(codeK + ';globalThis.Knowledge = Knowledge;');

(async () => {
  await Knowledge.init();

  /* ═══ 1. Base phyto chargée ═══ */
  section('Base phyto chargée dans Knowledge');
  ok(typeof Knowledge._phyto === 'object' && Object.keys(Knowledge._phyto).length >= 80,
    'Knowledge._phyto chargé (' + Object.keys(Knowledge._phyto).length + ' plantes)');
  ok(typeof Knowledge.getPhytoFor === 'function', 'Knowledge.getPhytoFor() exposé');
  ok(typeof Knowledge.getPhyto === 'function', 'Knowledge.getPhyto() exposé');

  /* ═══ 2. getPhytoFor — paludisme ═══ */
  section('getPhytoFor(["Paludisme_simple"])');
  const paluPlants = Knowledge.getPhytoFor(['Paludisme_simple']);
  ok(paluPlants.length >= 10, '≥ 10 plantes antipalustres (' + paluPlants.length + ')');
  // Tri : A avant B avant C, vigilance en dernier
  const paluGrades = paluPlants.map(p => p.grade_evidence);
  ok(paluGrades.includes('A'), 'au moins une plante grade A (Cryptolepis)');
  ok(paluGrades.includes('C'), 'plantes grade C présentes (traditionnel)');
  // Vérifie que le tri A>B>C est respecté sur le début de liste
  const firstA = paluPlants.findIndex(p => p.grade_evidence === 'A');
  const firstC = paluPlants.findIndex(p => p.grade_evidence === 'C' && p.niveau_recommandation !== 'vigilance');
  ok(firstA >= 0 && (firstC < 0 || firstA < firstC), 'grade A classé avant grade C');
  // Vigilance en dernier
  const vigIdx = paluPlants.findIndex(p => p.niveau_recommandation === 'vigilance');
  const lastCompl = paluPlants.map((p,i)=>p.niveau_recommandation==='complementaire'?i:-1).filter(i=>i>=0).pop();
  ok(vigIdx < 0 || lastCompl < 0 || vigIdx > lastCompl, 'plantes vigilance classées après complementaire');
  // indications_label présent
  ok(paluPlants.every(p => typeof p.indications_label === 'string'), 'indications_label enrichi sur chaque plante');
  // Artemisia en grade C avec précaution OMS
  const artemisia = paluPlants.find(p => /Artemisia/.test(p.nom_scientifique));
  ok(artemisia && artemisia.grade_evidence === 'C', 'Artemisia tisane = grade C (OMS déconseille)');
  ok(artemisia && /ACT|référence|OMS|résistance/.test(artemisia.precautions), 'Artemisia : précaution cite ACT/OMS');

  /* ═══ 3. getPhytoFor — dengue ═══ */
  section('getPhytoFor(["Dengue"])');
  const denguePlants = Knowledge.getPhytoFor(['Dengue']);
  ok(denguePlants.length >= 1, 'plantes pour la dengue (' + denguePlants.length + ')');
  const papaya = denguePlants.find(p => /Carica papaya/.test(p.nom_scientifique) && /feuille/i.test(p.partie_utilisee));
  ok(papaya && papaya.grade_evidence === 'A', 'Carica papaya (feuille) = grade A pour la dengue');

  /* ═══ 4. getPhytoFor — hypertension ═══ */
  section('getPhytoFor(["hypertension"])');
  const htaPlants = Knowledge.getPhytoFor(['hypertension']);
  ok(htaPlants.length >= 3, '≥ 3 plantes pour l\'HTA (' + htaPlants.length + ')');
  const hibiscus = htaPlants.find(p => /Hibiscus sabdariffa/.test(p.nom_scientifique));
  ok(hibiscus && hibiscus.grade_evidence === 'A', 'Hibiscus sabdariffa = grade A pour l\'HTA');

  /* ═══ 5. Matching robuste (accents/casse) ═══ */
  section('Matching robuste');
  // "Paludisme_simple" doit matcher même avec variations
  const v1 = Knowledge.getPhytoFor(['Paludisme_simple']);
  const v2 = Knowledge.getPhytoFor(['paludisme simple']);
  ok(v1.length > 0 && v2.length === v1.length, 'matching insensible à la casse/accents (Paludisme_simple vs "paludisme simple")');
  // Indication inconnue → vide
  ok(Knowledge.getPhytoFor(['Maladie_Inexistante_XYZ']).length === 0, 'indication inconnue → 0 plante');
  ok(Knowledge.getPhytoFor([]).length === 0, 'liste vide → 0 plante');

  /* ═══ 6. buildPhytoBox — encadré HTML ═══ */
  section('buildPhytoBox (encadré HTML)');
  // Recharge vital_ka_app.js pour buildPhytoBox (stub minimal du contexte)
  globalThis.currentPatient = null;
  // buildPhytoBox est défini dans vital_ka_app.js — on l'extrait par eval avec stubs
  const appCode = fs.readFileSync(path.join(__dirname, 'vital_ka_app.js'), 'utf8');
  // Capture uniquement buildPhytoBox (fonction autonome)
  const m = appCode.match(/function buildPhytoBox[\s\S]*?\n}/);
  if (m) {
    (0, eval)(m[0] + ';globalThis.buildPhytoBox = buildPhytoBox;');
    const box = buildPhytoBox([{ name: 'Paludisme_simple', score: 0.85 }]);
    ok(typeof box === 'string' && box.length > 0, 'buildPhytoBox retourne du HTML non vide');
    ok(box.includes('phyto-box'), 'encadré .phyto-box présent');
    ok(/ne remplace pas le traitement/i.test(box), 'avertissement « ne remplace pas » systématique');
    ok(box.includes('Grade A') || box.includes('grade A') || box.includes('phyto-grade-a'), 'badge grade présent');
    // Vigilance en rouge
    const boxVig = buildPhytoBox([{ name: 'Paludisme_simple', score: 0.85 }]);
    // Cryptolepis (A) doit figurer
    ok(/Cryptolepis/.test(box), 'Cryptolepis (grade A) affiché pour le paludisme');
  } else {
    ok(false, 'buildPhytoBox introuvable dans vital_ka_app.js');
  }

  /* ═══ 7. Désactivation (préférence soignant) ═══ */
  section('Désactivation encadré');
  localStorage.setItem('vital_ka_phyto_off', '1');
  const offBox = buildPhytoBox([{ name: 'Paludisme_simple', score: 0.85 }]);
  ok(offBox === '', 'localStorage vital_ka_phyto_off=1 → encadré désactivé (vide)');
  localStorage.removeItem('vital_ka_phyto_off');
  const onBox = buildPhytoBox([{ name: 'Paludisme_simple', score: 0.85 }]);
  ok(onBox.length > 0, 'encadré réactivé après suppression préférence');

  /* ═══ 8. Score pas pollué ═══ */
  section('Intégrité : phyto hors scoring');
  // La phyto n'est jamais ajoutée au DB de scoring
  ok(!Knowledge.getPhytoFor(['Paludisme_simple']).some(p => p.score !== undefined && typeof p.score === 'number' && p.score > 0.99),
    'les plantes ne portent pas de score diagnostique (jamais dans le top diagnostique)');

  /* ═══ Bilan ═══ */
  console.log('\n════════════════════════════════════════');
  console.log('BILAN : ' + passed + ' ✅ / ' + failed + ' ❌ (' + (passed + failed) + ' assertions)');
  process.exit(failed ? 1 : 0);
})();
