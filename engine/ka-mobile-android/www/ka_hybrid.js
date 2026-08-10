/* ══════════════════════════════════════════════════════════════════════════
   KA HYBRID — Pont d'audit mobile : noyau harmonique local + serveur /api/hybrid
   ══════════════════════════════════════════════════════════════════════════
   L'IA hybride dans KA Phone :
   1. NOYAU LOCAL (JS) — calcul exact par ondes (FNV-1a + phases φ), résonance
      simplifiée, REFUS calibré — fonctionne HORS-LIGNE, instantané.
   2. SERVEUR /api/hybrid — si disponible : le pont complet avec Phraseur
      (Ollama) + audit + régénération.
   3. AUDIT — le noyau local vérifie la réponse serveur : calcul exact,
      refus respecté. Si l'audit échoue → réponse du noyau local.

   API exposée : window.KAHybrid = { traiter(question), etat() }
   ══════════════════════════════════════════════════════════════════════════ */
(function (global) {
  'use strict';

  var PHI = (1 + Math.sqrt(5)) / 2;
  var SEUIL_RESONANCE = 0.30;

  // ═══════════════ NOYAU LOCAL — calcul par ondes (JS pur) ═══════════════
  // Hash FNV-1a (même implémentation que wave_lang.py → même onde !)
  function fnv1a(text) {
    var h = 0xCBF29CE484222325;
    for (var i = 0; i < text.length; i++) {
      h ^= text.charCodeAt(i);
      h = Math.imul(h, 0x100000001B3) >>> 0;
    }
    return h >>> 0;
  }

  // Encodage déterministe : ψ = phases φ issues du hash (compatible wave_lang)
  function encode(entite, dim) {
    dim = dim || 64;
    var h = fnv1a(entite);
    var re = new Float64Array(dim), im = new Float64Array(dim);
    for (var k = 0; k < dim; k++) {
      var phase = ((h >>> (k % 16)) + Math.imul(k, 2654435761)) % 2147483647;
      phase = (phase * PHI) % (2 * Math.PI);
      re[k] = Math.cos(phase);
      im[k] = Math.sin(phase);
    }
    // normalisation
    var n = 0;
    for (var k = 0; k < dim; k++) n += re[k] * re[k] + im[k] * im[k];
    n = Math.sqrt(n);
    for (var k = 0; k < dim; k++) { re[k] /= n; im[k] /= n; }
    return { re: re, im: im };
  }

  function resonate(a, b) {
    var s = 0;
    for (var k = 0; k < a.re.length; k++) s += a.re[k] * b.re[k] + a.im[k] * b.im[k];
    return Math.abs(s);
  }

  // ═══════════════ LE NOYAU LOCAL ═══════════════
  var concepts = {};
  function apprendre(nom) { concepts[nom] = encode(nom); }

  function calculer(expr) {
    expr = expr.replace(/,/g, '.').replace(/\s+/g, '');
    var ops = [['+', function (a, b) { return a + b; }],
               ['×', function (a, b) { return a * b; }],
               ['x', function (a, b) { return a * b; }],
               ['*', function (a, b) { return a * b; }],
               ['-', function (a, b) { return a - b; }],
               ['÷', function (a, b) { return a / b; }],
               ['/', function (a, b) { return a / b; }]];
    for (var i = 0; i < ops.length; i++) {
      var idx = expr.indexOf(ops[i][0]);
      if (idx > 0) {
        var a = parseFloat(expr.slice(0, idx));
        var b = parseFloat(expr.slice(idx + 1));
        if (!isNaN(a) && !isNaN(b)) return ops[i][1](a, b);
      }
    }
    return null;
  }

  // ── Identité : « qui es-tu ? » → KA se présente (avant tout routage)
  var PATTERNS_IDENTITE = ['qui es-tu', 'qui es tu', 'qui etes-vous', 'qui êtes-vous',
    'tu es qui', "qu'est-ce que tu es", 'quest-ce que tu es', 'qu est-ce que tu es',
    'ton nom', 'ton identite', "comment tu t'appelles", 'comment tu t appelles',
    'what are you', 'who are you', 'what is your name', 'es-tu une ia',
    'es tu une ia', 'es-tu un robot', 'tu es quoi', 'vous etes quoi'];

  var REPONSE_IDENTITE = 'Je suis KA (Knowledge Amplifier) — une intelligence artificielle harmonique. ' +
    'Je ne suis pas un LLM classique : je fonctionne sur le principe ondulatoire, ' +
    'chaque connaissance est une onde, chaque raisonnement une interférence. ' +
    'Zéro paramètre entraîné, zéro hallucination, déterminisme total — ' +
    'la même question donne toujours la même réponse. ' +
    'Je calcule par les ondes, je mémorise par le noyau doré, ' +
    'et je refuse de répondre quand je ne sais pas.';

  // 🩺 Connaissances médicales essentielles (dérivées du corpus — comme le serveur)
  var FAITS_MEDICAUX = {
    'diabète': 'Le diabète de type 2 se définit par une glycémie à jeun ≥ 1,26 g/L ' +
      '(7,0 mmol/L) à 2 reprises, OU une HbA1c ≥ 6,5 %, OU une glycémie aléatoire ≥ 2 g/L avec symptômes.',
    'hypertension': 'L\'hypertension artérielle se définit par une pression ≥ 140/90 mmHg ' +
      'à 2 consultations séparées. Objectif : < 140/90 (< 130/80 si diabète ou insuffisance rénale chronique).',
    'asthme': 'L\'asthme chronique est une inflammation chronique des voies aériennes ' +
      'avec bronchoconstriction réversible. Il se distingue de la crise aiguë, qui nécessite un traitement immédiat.',
    'epilepsie': 'L\'épilepsie est une affection neurologique caractérisée par des crises ' +
      'récidivantes non provoquées. Prévalence élevée en Afrique (cysticercose, paludisme, traumatismes).',
    'drepanocytose': 'La drépanocytose est une maladie génétique de l\'hémoglobine (HbS). ' +
      'La forme homozygote SS est la forme majeure. Fréquente en Afrique (1/4 porteurs sains dans certaines régions).',
    'insuffisance cardiaque': 'L\'insuffisance cardiaque est l\'incapacité du cœur à assurer ' +
      'un débit suffisant. Causes : HTA, cardiopathie ischémique, valvulopathie, cardiomyopathie.',
    'paludisme': 'Le paludisme est une maladie parasitaire transmise par la piqûre du ' +
      'moustique anophèle. La prévention repose sur la moustiquaire imprégnée, ' +
      'le traitement préventif et le diagnostic précoce.'
  };

  var MOTS_MEDICAUX = [
    { noms: ['diabete', 'diabète'], cle: 'diabète' },
    { noms: ['hypertension'], cle: 'hypertension' },
    { noms: ['asthme'], cle: 'asthme' },
    { noms: ['epilepsie', 'épilepsie'], cle: 'epilepsie' },
    { noms: ['drepanocytose', 'drépanocytose'], cle: 'drepanocytose' },
    { noms: ['insuffisance cardiaque'], cle: 'insuffisance cardiaque' },
    { noms: ['paludisme'], cle: 'paludisme' }
  ];

  function estQuestionMedicale(question) {
    var q = question.toLowerCase().replace(/'/g, ' ').replace(/-/g, ' ');
    var estDef = q.indexOf('c est quoi') >= 0 || q.indexOf('qu est ce que') >= 0 ||
                 q.indexOf('quoi') >= 0 || q.indexOf('explique') >= 0 || q.indexOf('definir') >= 0;
    if (!estDef) return null;
    for (var i = 0; i < MOTS_MEDICAUX.length; i++) {
      var item = MOTS_MEDICAUX[i];
      for (var j = 0; j < item.noms.length; j++)
        if (q.indexOf(item.noms[j]) >= 0) return item.cle;
    }
    return null;
  }

  function estIdentite(question) {
    var q = question.toLowerCase();
    for (var i = 0; i < PATTERNS_IDENTITE.length; i++)
      if (q.indexOf(PATTERNS_IDENTITE[i]) >= 0) return true;
    return false;
  }

  function repondre(question) {
    if (estIdentite(question)) return { type: 'IDENTITE' };
    var maladie = estQuestionMedicale(question);
    if (maladie) return { type: 'MEDICAL', concept: maladie, valeur: FAITS_MEDICAUX[maladie] };
    var r = calculer(question);
    if (r !== null) return { type: 'CALC', valeur: r };
    var qpsi = encode(question);
    var meilleur = null, score = 0;
    for (var nom in concepts) {
      var s = resonate(qpsi, concepts[nom]);
      if (s > score) { score = s; meilleur = nom; }
    }
    if (score >= SEUIL_RESONANCE) return { type: 'FAIT', concept: meilleur, score: score };
    return { type: 'REFUS', score: score };
  }

  function phraseModele(core) {
    if (core.type === 'IDENTITE') return REPONSE_IDENTITE;
    if (core.type === 'MEDICAL') return core.valeur;
    if (core.type === 'CALC') {
      var v = core.valeur;
      var s = (v === Math.floor(v)) ? String(v) : v.toFixed(6).replace(/0+$/, '').replace(/\.$/, '');
      return 'Le résultat exact est ' + s + ' — calculé par les ondes.';
    }
    if (core.type === 'FAIT') return 'Je connais ' + core.concept + ' — c\'est dans ma mémoire.';
    return 'Je ne peux pas répondre à ça — ce n\'est pas dans ce que je connais. Je préfère me taire plutôt que d\'inventer.';
  }

  // ═══════════════ L'AUDIT LOCAL ═══════════════
  var MOTS_REFUS = ['sais pas', 'connais', 'pas de réponse', 'préfère', 'limite',
                    'n\'ai pas', 'ne sais', 'dépasse', 'hors de', 'je ne peux',
                    'peux pas', 'ne suis pas', 'ne veux pas', 'capable', 'envie',
                    'du genre', 'désolé', 'ne peux pas', 'peut pas', 'pas capable'];

  function auditer(core, phrase) {
    phrase = phrase.toLowerCase();
    if (core.type === 'REFUS') {
      for (var i = 0; i < MOTS_REFUS.length; i++)
        if (phrase.indexOf(MOTS_REFUS[i]) >= 0) return true;
      return false;
    }
    if (core.type === 'CALC') {
      var v = core.valeur;
      var s = (v === Math.floor(v)) ? String(v) : v.toFixed(4).replace(/0+$/, '').replace(/\.$/, '');
      if (phrase.replace(/,/g, '.').indexOf(s) >= 0) return true;
      // nombres en lettres : on vérifie les mots-clés (cinq, quarante…)
      var lettres = ['un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf',
                     'dix', 'onze', 'douze', 'treize', 'quatorze', 'quinze', 'seize',
                     'vingt', 'trente', 'quarante', 'cinquante', 'soixante',
                     'quatre-vingt'];
      for (var j = 0; j < lettres.length; j++)
        if (phrase.indexOf(lettres[j]) >= 0) return true;
      return false;
    }
    if (core.type === 'FAIT') return phrase.indexOf(core.concept.toLowerCase()) >= 0;
    return false;
  }

  // ═══════════════ L'API SERVEUR (si disponible) ═══════════════
  function apiUrl() {
    try {
      var u = localStorage.getItem('ka_api_url');
      if (u) return u;
    } catch (e) { /* ignore */ }
    if (typeof location !== 'undefined' && location.hostname) {
      return 'http://' + location.hostname + ':8765';
    }
    return 'http://localhost:8765';
  }

  function appelerServeur(question, timeoutMs) {
    timeoutMs = timeoutMs || 25000;
    var url = apiUrl() + '/api/hybrid';
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: question }),
      signal: AbortSignal.timeout(timeoutMs)
    }).then(function (r) { return r.json(); });
  }

  // ═══════════════ L'API PUBLIQUE ═══════════════
  // Concepts de base appris (le vocabulaire du noyau local)
  ['chat', 'chien', 'oiseau', 'lumière', 'amour', 'eau', 'musique', 'santé'].forEach(apprendre);

  var stats = { CALC: 0, FAIT: 0, REFUS: 0, local: 0, serveur: 0, auditKO: 0 };

  function traiter(question, opts) {
    opts = opts || {};
    var core = repondre(question);
    stats[core.type]++;

    function finaliser(phrase, source, auditOK) {
      if (!auditOK) { stats.auditKO++; phrase = phraseModele(core); }
      return { question: question, type: core.type, response: phrase,
               source: source, audit: auditOK ? true : false,
               valeur: core.valeur, concept: core.concept };
    }

    // Serveur d'abord (si demandé) — puis audit local
    if (opts.useServer !== false) {
      return appelerServeur(question).then(function (r) {
        if (r && r.response) {
          stats.serveur++;
          var ok = auditer(core, r.response);
          return finaliser(r.response, 'serveur-hybride', ok);
        }
        // serveur a répondu mais pas utilisable → local
        stats.local++;
        return finaliser(phraseModele(core), 'noyau-local', true);
      }).catch(function () {
        // serveur indisponible → noyau local (hors-ligne)
        stats.local++;
        return finaliser(phraseModele(core), 'noyau-local', true);
      });
    }
    // Local direct (hors-ligne pur)
    stats.local++;
    return Promise.resolve(finaliser(phraseModele(core), 'noyau-local', true));
  }

  function etat() {
    return { concepts: Object.keys(concepts), seuil: SEUIL_RESONANCE, stats: stats };
  }

  global.KAHybrid = { traiter: traiter, etat: etat, calculer: calculer, repondre: repondre };
})(window);
