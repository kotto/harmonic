#!/usr/bin/env node
/* test_mobile_kernel.js — SUITE DE TESTS DU NOYAU MOBILE (KA Hybrid)
   ================================================================
   Exécute le protocole partagé (data/benchmarks/protocole_ka.json,
   écrit par tests_ka_hybride.py) contre le noyau local de KA Mobile
   (ka-mobile-android/www/ka_hybrid.js) — SANS serveur, SANS réseau.

   Usage : node test_mobile_kernel.js
   Le noyau mobile doit répondre exactement comme le pont serveur :
   la même question → le même type (déterminisme total).

   Critère : 100 % — chaque question doit produire le type attendu.
*/
'use strict';

var fs = require('fs');
var path = require('path');

// Shim navigateur minimal : ka_hybrid.js s'attache à `window`
global.window = global;

var KERNEL = path.join(__dirname, 'ka-mobile-android', 'www', 'ka_hybrid.js');
var PROTOCOLE = path.join(__dirname, 'data', 'benchmarks', 'protocole_ka.json');

require(KERNEL);
var K = global.KAHybrid;

var protocole = JSON.parse(fs.readFileSync(PROTOCOLE, 'utf8'));

var resultats = [];
for (var i = 0; i < protocole.length; i++) {
  var question = protocole[i][0];
  var attendu = protocole[i][1];
  var r = K.repondre(question);
  var ok = r.type === attendu;
  resultats.push({ question: question, attendu: attendu, obtenu: r.type, ok: ok });
}

var okCount = resultats.filter(function (r) { return r.ok; }).length;
var total = resultats.length;

console.log('='.repeat(66));
console.log('SUITE DE TESTS — NOYAU MOBILE (ka_hybrid.js, node)');
console.log('='.repeat(66));
console.log('  ' + total + ' questions · protocole partagé · critère : 100 %');
console.log('  RÉSULTAT : ' + okCount + '/' + total + '  ' + (okCount === total ? '✅' : '❌'));
console.log('');
console.log('  ' + 'Question'.padEnd(40) + ' ' + 'Attendu'.padEnd(10) + ' ' + 'Obtenu'.padEnd(10) + ' Statut');
console.log('  ' + '─'.repeat(72));
resultats.forEach(function (r) {
  var mark = r.ok ? '✅' : '❌';
  console.log('  ' + r.question.slice(0, 38).padEnd(40) + ' ' +
              r.attendu.padEnd(10) + ' ' + r.obtenu.padEnd(10) + ' ' + mark);
});
var echecs = resultats.filter(function (r) { return !r.ok; });
if (echecs.length) {
  console.log('\n  ⚠️ ' + echecs.length + ' ÉCHECS :');
  echecs.forEach(function (r) {
    console.log('    · « ' + r.question + ' » → attendu ' + r.attendu + ', obtenu ' + r.obtenu);
  });
}

// ══════════════════════════════════════════════════════════════════
// STYLE VOCAL — phrases modèles conversationnelles + vocalisation TTS
// ══════════════════════════════════════════════════════════════════
var SYMBOLES_NON_PARLES = ['—', '–', '→', '≥', '≤', '±', '⚠', '✅', '❌', '(', ')', '**'];
var vocal = { phrasePropre: true, vocalise: true, symboles: [] };

// 1. Les phrases modèles (ce que lira le synthétiseur) : zéro symbole
var CORES_TEST = [
  ['7 × 8', 'CALC'], ['12 + 34', 'CALC'], ['chat', 'FAIT'],
  ['quasar', 'REFUS'], ['raconte une blague', 'REFUS']];
CORES_TEST.forEach(function (c) {
  var core = K.repondre(c[0]);
  var phrase = K.phraseModele(core);
  SYMBOLES_NON_PARLES.forEach(function (s) {
    if (phrase.indexOf(s) >= 0) {
      vocal.phrasePropre = false;
      vocal.symboles.push({ question: c[0], symbole: s, phrase: phrase });
    }
  });
});

// 2. vocaliser() : les symboles réels du corpus deviennent des mots parlés
var CORPUS_VOCAL = '⚠️ URGENCE VITALE — Appeler le 15 IMMÉDIATEMENT. ' +
  'Glycémie ≥ 1,26 g/L (7,0 mmol/L) ; HbA1c ≥ 6,5 % ; ' +
  'pression 140/90 mmHg ; 40-60 insufflations/min ; 2x/j ; ' +
  'fièvre > 38,5 °C. → Hospitalisation. 24h/24, 7j/7.';
var exigencesVocales = [
  'supérieur ou égal à', 'grammes par litre', 'millimoles par litre',
  'hémoglobine glyquée', 'pour cent', 'sur 90', 'millimètres de mercure',
  'de 40 à 60', 'fois par jour', 'plus de 38,5', 'degrés',
  '24 heures sur 24', '7 jours sur 7', 'Hospitalisation'];
var symbResiduels = ['≥', '→', '—', '⚠', '(', ')', 'g/L', '%', '/', '°', '**'];

if (typeof K.vocaliser !== 'function') {
  vocal.vocalise = false;
} else {
  var v = K.vocaliser(CORPUS_VOCAL);
  exigencesVocales.forEach(function (e) {
    if (v.indexOf(e) < 0) {
      vocal.vocalise = false;
      vocal.symboles.push({ exigence: e, obtenu: v.slice(0, 80) });
    }
  });
  symbResiduels.forEach(function (s) {
    if (v.indexOf(s) >= 0) {
      vocal.vocalise = false;
      vocal.symboles.push({ symboleResiduel: s, obtenu: v.slice(0, 80) });
    }
  });
}

console.log('\n  STYLE VOCAL (mobile) :');
console.log('    phrases modèles sans symbole : ' + (vocal.phrasePropre ? '✅' : '❌'));
console.log('    vocaliser() corpus → parole  : ' + (vocal.vocalise ? '✅' : '❌'));
if (vocal.symboles.length) {
  console.log('    ⚠️ ' + JSON.stringify(vocal.symboles).slice(0, 200));
}

// Rapport
var rapp = {
  protocole: total + ' questions pré-enregistrées, critère 100 %',
  plateforme: 'mobile (ka_hybrid.js — noyau local node)',
  ok: okCount,
  total: total,
  vocal: { phrasePropre: vocal.phrasePropre, vocalise: vocal.vocalise,
           symboles: vocal.symboles },
  date: new Date().toISOString().slice(0, 19).replace('T', ' '),
  resultats: resultats
};
var p = path.join(__dirname, 'data', 'benchmarks', 'tests_ka_mobile_report.json');
fs.writeFileSync(p, JSON.stringify(rapp, null, 2), 'utf8');
console.log('\nRapport : ' + p);

if (okCount !== total || !vocal.phrasePropre || !vocal.vocalise) {
  console.log('\n❌ SUITE NON PASSÉE — corriger les échecs avant validation.');
  process.exit(1);
}
console.log('\n✅ SUITE PASSÉE — le noyau mobile est validé sur ' + total + ' questions.');
console.log('   Style vocal validé : phrases conversationnelles lisibles par le synthétiseur.');
