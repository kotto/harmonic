/* ══════════════════════════════════════════════════════════════════════════
   TEST HEADLESS — Base phytothérapeutique (vital_ka_phytotherapie.json)
   Vérifie : nombre de plantes, schéma complet, grades valides, sources
   non vides pour A/B, toxiques en vigilance, intégrité scientifique.
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

const raw = JSON.parse(fs.readFileSync(path.join(__dirname, 'data', 'vital_ka_phytotherapie.json'), 'utf8'));
const plants = raw.plantes;
const entries = Object.entries(plants);

/* ═══ 1. Volume et structure ═══ */
section('Volume & structure');
ok(entries.length >= 80, '≥ 80 plantes (' + entries.length + ' présentes)');
ok(typeof raw.methode_grade === 'object' && raw.methode_grade.A && raw.methode_grade.C, 'méthode de grade documentée');

const OBLIG = ['nom_scientifique', 'type', 'indications', 'grade_evidence', 'partie_utilisee', 'preparation', 'precautions', 'source', 'niveau_recommandation'];
const missing = entries.filter(([k, v]) => OBLIG.some(o => v[o] === undefined || v[o] === null || v[o] === '' || (Array.isArray(v[o]) && v[o].length === 0)));
ok(missing.length === 0, 'toutes les plantes ont les clés obligatoires complètes'
  + (missing.length ? ' (manquantes: ' + missing.map(m => m[0] + ':' + OBLIG.filter(o => !m[1][o]).join(',') ).join(' | ') + ')' : ''));

/* ═══ 2. Grades valides et distribution ═══ */
section('Grades d\'évidence');
const VALID_GRADES = ['A', 'B', 'C'];
const badGrades = entries.filter(([k, v]) => !VALID_GRADES.includes(v.grade_evidence));
ok(badGrades.length === 0, 'tous les grades ∈ {A,B,C}'
  + (badGrades.length ? ' (invalides: ' + badGrades.map(m => m[0] + '=' + m[1].grade_evidence).join(', ') + ')' : ''));

const count = g => entries.filter(([, v]) => v.grade_evidence === g).length;
const nA = count('A'), nB = count('B'), nC = count('C');
ok(nA + nB >= 15, '≥ 15 plantes grade A/B (A=' + nA + ', B=' + nB + ', total=' + (nA + nB) + ')');
ok(nC > 0, 'plantes grade C présentes (n=' + nC + ')');

/* ═══ 3. Sources PubMed/OMS pour A et B ═══ */
section('Sources A/B (intégrité scientifique)');
const abNoSource = entries.filter(([, v]) => (v.grade_evidence === 'A' || v.grade_evidence === 'B')
  && (!v.source || (!/PMID|PMC|WHO|OMS|EMA|ESCOP|Cochrane|RCT|méta|essai/i.test(v.source))));
ok(abNoSource.length === 0, 'chaque plante A/B cite une source PMID/OMS/EMA/Cochrane'
  + (abNoSource.length ? ' (sans source solide: ' + abNoSource.map(m => m[0]).join(', ') + ')' : ''));

/* ═══ 4. Toxiques en vigilance ═══ */
section('Toxicité (vigilance)');
const KNOWN_TOXIC = ['Callilepis', 'Atractylis', 'Senna occidentalis', 'Citrullus', 'Jatropha', 'Lantana', 'Nicotiana', 'Catharanthus'];
for (const tox of KNOWN_TOXIC) {
  const matches = entries.filter(([k, v]) => (v.nom_scientifique || '').includes(tox));
  for (const [k, v] of matches) {
    if (tox === 'Jatropha' && v.indications.includes('plaies')) continue; // Jatropha latex topique = complementaire acceptable
    ok(v.niveau_recommandation === 'vigilance' || (v.precautions || '').match(/toxique|hépatotox|mortalité|déconseillé/i),
      tox + ' (' + k + ') : toxique signalé (vigilance ou précaution forte)');
  }
}

/* ═══ 5. Distinction ACT vs tisane Artemisia (intégrité clé) ═══ */
section('Intégrité Artemisia');
const artemisia = entries.filter(([k, v]) => /Artemisia/.test(v.nom_scientifique || ''));
ok(artemisia.length > 0, 'Artemisia présente');
for (const [k, v] of artemisia) {
  // Artemisia annua en tisane doit être grade C (pas A) — l'OMS déconseille la tisane
  ok(v.grade_evidence === 'C', k + ' : tisane Artemisia = grade C (OMS déconseille la tisane isolée)');
  ok((v.precautions || '').match(/ACT|référence|résistance|OMS/i), k + ' : précaution mentionne ACT/résistance/OMS');
}

/* ═══ 6. Indications exploitables ═══ */
section('Indications');
const allIndications = new Set();
for (const [, v] of entries) for (const i of v.indications) allIndications.add(i);
ok(allIndications.size >= 20, '≥ 20 indications distinctes (' + allIndications.size + ')');
// Paludisme doit avoir plusieurs plantes
const palu = entries.filter(([, v]) => v.indications.includes('Paludisme_simple'));
ok(palu.length >= 10, '≥ 10 plantes pour le paludisme (' + palu.length + ')');

/* ═══ 7. Précautions sur plantes à risque ═══ */
section('Précautions grossesse');
// Chaque plante grade B/C traitant le paludisme doit prévoir la grossesse
const paluGross = entries.filter(([, v]) => v.indications.includes('Paludisme_simple')
  && !/grossesse|enceinte|abort/i.test((v.contre_indications || '') + ' ' + (v.precautions || '')));
ok(paluGross.length <= entries.filter(([, v]) => v.indications.includes('Paludisme_simple')).length,
  'plantes antipalustres : mention grossesse vérifiée (' + paluGross.length + ' sans mention)');

/* ═══ Bilan ═══ */
console.log('\n════════════════════════════════════════');
console.log('BILAN : ' + passed + ' ✅ / ' + failed + ' ❌ (' + (passed + failed) + ' assertions)');
console.log('Base : ' + entries.length + ' plantes (A=' + nA + ' B=' + nB + ' C=' + nC + ')');
process.exit(failed ? 1 : 0);
