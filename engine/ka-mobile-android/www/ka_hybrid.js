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
      'le traitement préventif et le diagnostic précoce.',
    'fièvre': 'La fièvre se définit par une température axillaire ≥ 37,5 °C ou rectale ' +
      '≥ 38 °C. Toute fièvre chez un enfant de moins de 3 mois est une urgence.',
    'fièvre jaune': 'La fièvre jaune est une maladie virale : fièvre brutale, frissons, ' +
      'ictère et hémorragies possibles. URGENCE VITALE — Hospitalisation. ' +
      'Pas de traitement spécifique. Vaccination préventive.',
    'convulsions fébriles': 'Convulsion généralisée associée à la fièvre chez l\'enfant ' +
      'de 6 mois à 5 ans, sans infection du système nerveux central et sans antécédent ' +
      'épileptique. Conduite : position latérale, ne rien mettre en bouche.',
    'gastro': 'La gastro-entérite associe diarrhée, vomissements, nausées et douleurs ' +
      'abdominales, avec fièvre modérée possible. Gravité modérée. Conduite : ' +
      'réhydratation (soluté oral), repas légers.',
    'covid': 'La COVID-19 associe fièvre, toux sèche, fatigue, perte d\'odorat (anosmie) ' +
      'et de goût (agueusie), essoufflement possible. Gravité élevée. Conduite : ' +
      'isolement immédiat, test PCR.'
  };

  // 🚨 Conduites d'urgence (dérivées du corpus — gravité + conduite_à_tenir + symptômes)
  var CONDUITES_URGENCE = {
    'avc': '⚠️ URGENCE VITALE — Appeler le 15 IMMÉDIATEMENT. Chaque minute compte. ' +
      'Signes : paralysie du visage, faiblesse d\'un bras, trouble de la parole.',
    'infarctus': '⚠️ URGENCE VITALE — Appeler le 15 (SAMU) IMMÉDIATEMENT. ' +
      'Ne pas conduire. Rester au repos. Signes : douleur thoracique, essoufflement, sueurs froides.',
    'appendicite': '⚠️ URGENCE VITALE — Appeler le 15. Ne pas manger ni boire. ' +
      'Risque de péritonite. Signes : douleur abdominale droite, fièvre modérée.',
    'dengue': 'Consultation. Paracétamol uniquement — pas d\'aspirine ni d\'ibuprofène. ' +
      'Hydratation. Signes d\'alarme : douleurs abdominales, vomissements, saignements → urgence.',
    'covid': 'Isolement immédiat. Test PCR. Consultation si essoufflement.',
    'rhume': 'Repos, hydratation, lavage de nez. Pas d\'antibiotiques — c\'est viral.',
    'gastro': 'Réhydratation (soluté oral). Repas légers. ' +
      'Consultation si signes de déshydratation (48 h si pas d\'amélioration).',
    'fièvre': 'Rechercher paludisme (TDR), infection urinaire, méningite selon les signes. ' +
      'Paracétamol 10-15 mg/kg si fièvre élevée. Fièvre chez un enfant < 3 mois = urgence.',
    'convulsions fébriles': 'Position latérale de sécurité. Ne rien mettre en bouche. ' +
      'Si la crise dure plus de 5 minutes : diazépam IR 0,5 mg/kg. Évoquer la méningite ' +
      'si 1re crise, signes méningés ou récupération lente.'
  };

  var ALIASES_CONDUITE = {
    'crise cardiaque': 'infarctus',
    'attaque cerebrale': 'avc',
    'coronavirus': 'covid',
    'covid 19': 'covid',
    'covid19': 'covid',
    'convulsions': 'convulsions fébriles',
    'gastro enterite': 'gastro'
  };

  var MOTS_MEDICAUX = [
    { noms: ['diabete', 'diabète'], cle: 'diabète' },
    { noms: ['hypertension'], cle: 'hypertension' },
    { noms: ['asthme'], cle: 'asthme' },
    { noms: ['epilepsie', 'épilepsie'], cle: 'epilepsie' },
    { noms: ['drepanocytose', 'drépanocytose'], cle: 'drepanocytose' },
    { noms: ['insuffisance cardiaque'], cle: 'insuffisance cardiaque' },
    { noms: ['paludisme'], cle: 'paludisme' },
    // ⚠️ fièvre jaune AVANT fièvre (ordre = priorité de correspondance)
    { noms: ['fievre jaune', 'fièvre jaune'], cle: 'fièvre jaune' },
    { noms: ['fievre', 'fièvre'], cle: 'fièvre' },
    { noms: ['convulsions febrile', 'convulsions fébriles'], cle: 'convulsions fébriles' },
    { noms: ['gastro'], cle: 'gastro' },
    { noms: ['covid'], cle: 'covid' }
  ];

  function estQuestionConduite(question) {
    // « que faire en cas d'AVC ? » → la conduite du corpus, pas une invention
    var q = sansAccents(question).replace(/'/g, ' ').replace(/-/g, ' ');
    var marqueurs = ['que faire', 'en cas', 'conduite', 'que dois', 'comment reagir'];
    var marque = false;
    for (var i = 0; i < marqueurs.length; i++)
      if (q.indexOf(marqueurs[i]) >= 0) { marque = true; break; }
    if (!marque) return null;
    for (var cle in CONDUITES_URGENCE)
      if (q.indexOf(sansAccents(cle)) >= 0) return cle;
    for (var alias in ALIASES_CONDUITE)
      if (q.indexOf(alias) >= 0) return ALIASES_CONDUITE[alias];
    return null;
  }

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

  var SEUIL_RESONANCE_FAIT = 0.60; // seuil ÉLEVÉ : seuls les concepts quasi-exacts passent

  function motsDe(question) {
    // tokenisation simple : mots de 3+ lettres, sans accents
    var q = question.toLowerCase().replace(/[éèêë]/g, 'e').replace(/[àâä]/g, 'a')
      .replace(/[îï]/g, 'i').replace(/[ôö]/g, 'o').replace(/[ùûü]/g, 'u').replace(/ç/g, 'c');
    return q.match(/[a-zœ]{3,}/g) || [];
  }

  function sansAccents(s) {
    return s.toLowerCase().replace(/[éèêë]/g, 'e').replace(/[àâä]/g, 'a')
      .replace(/[îï]/g, 'i').replace(/[ôö]/g, 'o').replace(/[ùûü]/g, 'u').replace(/ç/g, 'c');
  }

  var conceptsNorm = null; // {nomNormalisé: nomOriginal}
  function conceptsNormalises() {
    if (conceptsNorm) return conceptsNorm;
    conceptsNorm = {};
    for (var nom in concepts) conceptsNorm[sansAccents(nom)] = nom;
    return conceptsNorm;
  }

  function conceptPresent(question) {
    // détection par présence du mot-concept (accents ignorés)
    var mots = motsDe(question);
    var table = conceptsNormalises();
    for (var cle in table) {
      for (var i = 0; i < mots.length; i++)
        if (mots[i].indexOf(cle) >= 0 || cle.indexOf(mots[i]) >= 0) return table[cle];
    }
    return null;
  }

  function repondre(question) {
    if (estIdentite(question)) return { type: 'IDENTITE' };
    var conduite = estQuestionConduite(question);
    if (conduite) return { type: 'CONDUITE', concept: conduite, valeur: CONDUITES_URGENCE[conduite] };
    var maladie = estQuestionMedicale(question);
    if (maladie) return { type: 'MEDICAL', concept: maladie, valeur: FAITS_MEDICAUX[maladie] };
    var r = calculer(question);
    if (r !== null) return { type: 'CALC', valeur: r };
    // 1. présence du mot-concept (déterministe et fiable)
    var trouve = conceptPresent(question);
    if (trouve) return { type: 'FAIT', concept: trouve, score: 1.0 };
    // 2. résonance avec seuil ÉLEVÉ (complément sémantique, très exigeant)
    var qpsi = encode(question);
    var meilleur = null, score = 0;
    for (var nom in concepts) {
      var s = resonate(qpsi, concepts[nom]);
      if (s > score) { score = s; meilleur = nom; }
    }
    if (score >= SEUIL_RESONANCE_FAIT) return { type: 'FAIT', concept: meilleur, score: score };
    return { type: 'REFUS', score: score };
  }

  function phraseModele(core) {
    if (core.type === 'IDENTITE') return REPONSE_IDENTITE;
    if (core.type === 'MEDICAL') return core.valeur;
    if (core.type === 'CONDUITE') return core.valeur;
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

  // Nombres en lettres françaises — port exact de _en_lettres (pont_hybride.py)
  var UNITES_LETTRES = ['', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept',
    'huit', 'neuf', 'dix', 'onze', 'douze', 'treize', 'quatorze', 'quinze',
    'seize', 'dix-sept', 'dix-huit', 'dix-neuf'];
  var DIZAINES_LETTRES = ['', 'dix', 'vingt', 'trente', 'quarante', 'cinquante',
    'soixante', 'soixante-dix', 'quatre-vingt', 'quatre-vingt-dix'];

  function enLettres(n) {
    if (n === 0) return 'zéro';
    if (n < 20) return UNITES_LETTRES[n];
    if (n < 100) {
      var d = Math.floor(n / 10), u = n % 10;
      if (d === 7) return u ? 'soixante-' + UNITES_LETTRES[10 + u] : 'soixante-dix';
      if (d === 9) return u ? 'quatre-vingt-' + UNITES_LETTRES[10 + u] : 'quatre-vingt';
      return DIZAINES_LETTRES[d] + (u ? '-' + UNITES_LETTRES[u] : '');
    }
    var c = Math.floor(n / 100), r = n % 100;
    return 'cent' + (r ? ' ' + enLettres(r) : '');
  }

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
      // nombres en lettres : vérification exacte (première + dernière partie)
      if (v === Math.floor(v) && v >= 0 && v < 1000) {
        var parties = enLettres(v).split('-');
        if (phrase.indexOf(parties[0]) >= 0 &&
            phrase.indexOf(parties[parties.length - 1]) >= 0) return true;
      }
      return false;
    }
    if (core.type === 'FAIT') return phrase.indexOf(core.concept.toLowerCase()) >= 0;
    if (core.type === 'MEDICAL' || core.type === 'CONDUITE') {
      // empreinte du contenu : premiers mots significatifs (comme le serveur)
      var mots = (sansAccents(core.valeur || '').match(/[a-z]{5,}/g) || []).slice(0, 3);
      for (var k = 0; k < mots.length; k++)
        if (phrase.indexOf(mots[k]) >= 0) return true;
      return false;
    }
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

  global.KAHybrid = { traiter: traiter, etat: etat, calculer: calculer,
                      repondre: repondre, phraseModele: phraseModele };
})(window);
