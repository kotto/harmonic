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

// Rapport
var rapp = {
  protocole: total + ' questions pré-enregistrées, critère 100 %',
  plateforme: 'mobile (ka_hybrid.js — noyau local node)',
  ok: okCount,
  total: total,
  date: new Date().toISOString().slice(0, 19).replace('T', ' '),
  resultats: resultats
};
var p = path.join(__dirname, 'data', 'benchmarks', 'tests_ka_mobile_report.json');
fs.writeFileSync(p, JSON.stringify(rapp, null, 2), 'utf8');
console.log('\nRapport : ' + p);

if (okCount !== total) {
  console.log('\n❌ SUITE NON PASSÉE — corriger les échecs avant validation.');
  process.exit(1);
}
console.log('\n✅ SUITE PASSÉE — le noyau mobile est validé sur ' + total + ' questions.');
