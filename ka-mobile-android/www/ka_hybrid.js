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

  // ── Historique conversationnel (5 derniers échanges) ──
  var history = [];

  // ── Identité : « qui es-tu ? » → KA se présente (avant tout routage)
  var PATTERNS_IDENTITE = ['qui es-tu', 'qui es tu', 'qui etes-vous', 'qui êtes-vous',
    'qui etes vous', 'qui êtes vous', 'tu es qui', "qu'est-ce que tu es", 'quest-ce que tu es',
    'qu est-ce que tu es', 'qu est ce que tu es',
    'ton nom', 'ton identite', "comment tu t'appelles", 'comment tu t appelles',
    'comment t appelles tu',
    'what are you', 'who are you', 'what is your name', 'es-tu une ia',
    'es tu une ia', 'es-tu un robot', 'tu es quoi', 'vous etes quoi', 'vous êtes quoi',
    'presente toi', 'présente toi', 'presentez vous', 'présentez vous'];

  var REPONSES_IDENTITE = [
    // Courte
    'KA — Knowledge Amplifier. IA harmonique, déterministe, hors-ligne. Je réponds sans halluciner.',
    // Longue
    'Je suis KA (Knowledge Amplifier) — une intelligence artificielle harmonique. Je ne suis pas un LLM classique : je fonctionne sur le principe ondulatoire, chaque connaissance est une onde, chaque raisonnement une interférence. Zéro paramètre entraîné, zéro hallucination, déterminisme total — la même question donne toujours la même réponse.',
    // Technique
    'KA : noyau harmonique local (FNV-1a + phases φ, 64 dimensions). Calculateur par ondes, résonance de concepts, refus calibré. Zéro hallucination, zéro paramètre entraîné, déterministe. Instantané (0.03 ms).'
  ];

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
      'isolement immédiat, test PCR.',
    // +8 pathologies Afrique (Phase 1)
    'vih': 'Le VIH (Virus de l\'Immunodéficience Humaine) est un rétrovirus qui attaque ' +
      'les lymphocytes CD4. Sans traitement antirétroviral, il évolue vers le SIDA. ' +
      'Prévalence élevée en Afrique subsaharienne. Le traitement antirétroviral (ARV) ' +
      'permet une vie normale et réduit la transmission à 0 % (charge virale indétectable).',
    'tuberculose': 'La tuberculose est une infection bactérienne (Mycobacterium tuberculosis) ' +
      'touchant principalement les poumons. Transmission aérienne (toux). ' +
      'Traitement : antibiothérapie de 6 mois (rifampicine, isoniazide, pyrazinamide, éthambutol). ' +
      'L\'Afrique représente 25 % des cas mondiaux.',
    'méningite': 'La méningite est une inflammation des méninges, d\'origine infectieuse ' +
      '(bactérienne, virale ou fongique). Signes : fièvre, raideur de la nuque, ' +
      'céphalées, photophobie. URGENCE VITALE si bactérienne — antibiothérapie immédiate. ' +
      'La ceinture de la méningite en Afrique subsaharienne est particulièrement touchée.',
    'hépatite': 'L\'hépatite est une inflammation du foie. Les types B et C sont les plus ' +
      'graves (risque de cirrhose et cancer du foie). L\'hépatite B est endémique en Afrique ' +
      '(plus de 60 millions de porteurs chroniques). Vaccination efficace disponible.',
    'malnutrition': 'La malnutrition est un déséquilibre nutritionnel incluant la dénutrition ' +
      'et les carences en micronutriments. La malnutrition aiguë sévère (MAS) se définit par ' +
      'un périmètre brachial < 115 mm chez l\'enfant. Prise en charge : aliments thérapeutiques ' +
      'prêts à l\'emploi (ATPE), supplémentation en vitamine A, zinc.',
    'anémie': 'L\'anémie se définit par un taux d\'hémoglobine < 13 g/dL (homme) ou < 12 g/dL ' +
      '(femme). Causes fréquentes en Afrique : carence en fer (alimentation), paludisme, ' +
      'drépanocytose, parasitoses intestinales. Traitement : fer oral, traitement de la cause.',
    'bilharziose': 'La bilharziose (schistosomiase) est une parasitose due à des vers plats ' +
      '(Schistosoma). Transmission par l\'eau douce contaminée. Symptômes : hématurie, ' +
      'fibrose hépatique, hypertension portale. Endémique en Afrique (200 millions de cas). ' +
      'Traitement : praziquantel en dose unique.',
    'choléra': 'Le choléra est une infection diarrhéique aiguë due à Vibrio cholerae. ' +
      'Transmission par eau et aliments contaminés. Risque de déshydratation rapide et mortelle. ' +
      'Traitement : réhydratation orale (SRO) ou intraveineuse, antibiothérapie. ' +
      'Prévention : eau potable, hygiène, vaccin oral.'
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
      'si 1re crise, signes méningés ou récupération lente.',
    // +5 urgences (Phase 1)
    'brûlure': '⚠️ URGENCE — Refroidir immédiatement à l\'eau tiède (15-20 min). ' +
      'Ne pas percer les cloques. Couvrir d\'un linge propre. Brûlure grave (3e degré, > 10 % surface) : ' +
      'Appeler le 15. Signes de gravité : phlyctènes, carbonisation, choc.',
    'noyade': '⚠️ URGENCE VITALE — Appeler le 15. Sortir l\'eau. Vérifier conscience et respiration. ' +
      'Si inconscient et ne respire pas : RCP immédiate (30 compressions / 2 insufflations). ' +
      'Protéger la colonne cervicale si suspicion de traumatisme.',
    'serpent': '⚠️ URGENCE — Appeler le 15 ou centre antipoison. Immobiliser le membre mordu. ' +
      'Ne pas inciser, ne pas sucer, ne pas poser de garrot. Retirer bagues et montres. ' +
      'Noter l\'aspect du serpent si possible. Antivenin spécifique nécessaire.',
    'intoxication': '⚠️ URGENCE — Appeler le 15 ou centre antipoison (CAP). ' +
      'Ne pas faire vomir sans avis médical. Conserver l\'emballage du produit ingéré. ' +
      'Signes de gravité : troubles de conscience, convulsions, détresse respiratoire.',
    'hémorragie': '⚠️ URGENCE VITALE — Appeler le 15. Compression directe sur la plaie avec un ' +
      'linge propre. Surélever le membre si possible. Allonger la personne. ' +
      'Signes de choc hémorragique : pâleur, sueurs, pouls rapide, hypotension.'
  };

  var ALIASES_CONDUITE = {
    'crise cardiaque': 'infarctus',
    'attaque cerebrale': 'avc',
    'coronavirus': 'covid',
    'covid 19': 'covid',
    'covid19': 'covid',
    'convulsions': 'convulsions fébriles',
    'gastro enterite': 'gastro',
    'brulure': 'brûlure',
    'morsure serpent': 'serpent',
    'morsure de serpent': 'serpent'
  };

  var MOTS_MEDICAUX = [
    { noms: ['diabete', 'diabète', 'diabetes'], cle: 'diabète' },
    { noms: ['hypertension', 'hta', 'high blood pressure'], cle: 'hypertension' },
    { noms: ['asthme', 'asthma'], cle: 'asthme' },
    { noms: ['epilepsie', 'épilepsie', 'epilepsy'], cle: 'epilepsie' },
    { noms: ['drepanocytose', 'drépanocytose', 'sickle cell'], cle: 'drepanocytose' },
    { noms: ['insuffisance cardiaque', 'heart failure'], cle: 'insuffisance cardiaque' },
    { noms: ['paludisme', 'malaria'], cle: 'paludisme' },
    // ⚠️ fièvre jaune AVANT fièvre (ordre = priorité de correspondance)
    { noms: ['fievre jaune', 'fièvre jaune', 'yellow fever'], cle: 'fièvre jaune' },
    { noms: ['fievre', 'fièvre', 'fever'], cle: 'fièvre' },
    { noms: ['convulsions febrile', 'convulsions fébriles', 'febrile seizures'], cle: 'convulsions fébriles' },
    { noms: ['gastro', 'gastroenterite', 'gastro-entérite'], cle: 'gastro' },
    { noms: ['covid', 'covid-19', 'covid19', 'coronavirus'], cle: 'covid' },
    // +8 pathologies (Phase 1)
    { noms: ['vih', 'sida', 'vih sida', 'vih/sida', 'hiv', 'aids'], cle: 'vih' },
    { noms: ['tuberculose', 'tuberculosis', 'tb'], cle: 'tuberculose' },
    { noms: ['méningite', 'meningite', 'meningitis'], cle: 'méningite' },
    { noms: ['hépatite', 'hepatite', 'hepatitis'], cle: 'hépatite' },
    { noms: ['malnutrition', 'undernutrition'], cle: 'malnutrition' },
    { noms: ['anémie', 'anemie', 'anemia'], cle: 'anémie' },
    { noms: ['bilharziose', 'schistosomiase', 'bilharzia'], cle: 'bilharziose' },
    { noms: ['choléra', 'cholera'], cle: 'choléra' }
  ];

  // ── FAQ Connaissances générales (Phase 1) ──
  var FAQ = {
    'capitale france': 'La capitale de la France est Paris.',
    'capitale fr': 'La capitale de la France est Paris.',
    'capitale congo': 'La capitale de la République Démocratique du Congo est Kinshasa. ' +
      'La capitale du Congo-Brazzaville est Brazzaville.',
    'capitale cote ivoire': 'La capitale de la Côte d\'Ivoire est Yamoussoukro. Abidjan est la capitale économique.',
    'hauteur tour eiffel': 'La tour Eiffel mesure 330 mètres (antenne incluse). Construite en 1889 pour l\'exposition universelle.',
    'population terre': 'La population mondiale est d\'environ 8,2 milliards d\'habitants (2026).',
    'symbole eau': 'Le symbole chimique de l\'eau est H2O. Une molécule d\'eau contient deux atomes d\'hydrogène et un atome d\'oxygène.',
    'vitesse lumiere': 'La vitesse de la lumière dans le vide est d\'environ 299 792 458 mètres par seconde (3 × 10^8 m/s).',
    'inventeur telephone': 'Le téléphone a été inventé par Alexander Graham Bell en 1876.',
    'inventeur ampoule': 'L\'ampoule électrique a été perfectionnée par Thomas Edison en 1879.',
    'premier homme lune': 'Le premier homme à avoir marché sur la Lune est Neil Armstrong le 21 juillet 1969 (mission Apollo 11).',
    'plus haut sommet': 'Le plus haut sommet du monde est l\'Everest (8 849 m), dans l\'Himalaya, à la frontière du Népal et du Tibet.',
    'plus long fleuve': 'Le plus long fleuve du monde est l\'Amazone (environ 7 000 km), suivi du Nil (6 850 km).',
    'nombre or': 'Le nombre d\'or, noté φ (phi), vaut (1 + √5)/2 ≈ 1,618 033 988 749 895… C\'est la constante fondamentale de la Théorie Harmonique.',
  };

  var FAQ_PATTERNS = {};
  for (var faqKey in FAQ) {
    var parts = faqKey.split(' ');
    var motsCle = [];
    for (var pi = 0; pi < parts.length; pi++) {
      motsCle.push(parts[pi]);
    }
    FAQ_PATTERNS[faqKey] = motsCle;
  }

  function estQuestionFAQ(question) {
    var q = sansAccents(question);
    for (var cle in FAQ_PATTERNS) {
      var ok = true;
      var patternMots = FAQ_PATTERNS[cle];
      for (var pj = 0; pj < patternMots.length; pj++) {
        if (q.indexOf(patternMots[pj]) < 0) { ok = false; break; }
      }
      if (ok) return cle;
    }
    return null;
  }

  function estQuestionConduite(question) {
    // « que faire en cas d'AVC ? » → la conduite du corpus, pas une invention
    var q = sansAccents(question).replace(/'/g, ' ').replace(/-/g, ' ');
    var marqueurs = ['que faire', 'en cas', 'conduite', 'que dois', 'comment reagir', 'crise', 'urgence', 'que faire si'];
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
    var q = sansAccents(question.replace(/'/g, ' ').replace(/-/g, ' '));
    var estDef = q.indexOf('c est quoi') >= 0 || q.indexOf('qu est ce que') >= 0 ||
                 q.indexOf('quoi') >= 0 || q.indexOf('explique') >= 0 || q.indexOf('definir') >= 0 ||
                 q.indexOf('defini') >= 0 || q.indexOf('symptome') >= 0 || q.indexOf('traitement') >= 0 ||
                 q.indexOf('cause') >= 0 || q.indexOf('diagnostic') >= 0 ||
                 q.indexOf('what is') >= 0 || q.indexOf('what are') >= 0 || q.indexOf('what does') >= 0 ||
                 q.indexOf('define') >= 0 || q.indexOf('describe') >= 0 || q.indexOf('explain') >= 0 ||
                 q.indexOf('tell me about') >= 0 || q.indexOf('whats') >= 0 ||
                 q.indexOf('symptom') >= 0 || q.indexOf('treatment') >= 0 || q.indexOf('cause of') >= 0;
    if (!estDef) return null;
    for (var i = 0; i < MOTS_MEDICAUX.length; i++) {
      var item = MOTS_MEDICAUX[i];
      for (var j = 0; j < item.noms.length; j++)
        if (q.indexOf(item.noms[j]) >= 0) return item.cle;
    }
    return null;
  }

  // ── Phase 3 : Détection directe des mots de pathologies ──
  // Si l'utilisateur tape juste « diabète » sans marqueur de définition
  var MOTS_PATHOLOGIES_DIRECTS = {};
  for (var mi = 0; mi < MOTS_MEDICAUX.length; mi++) {
    var item = MOTS_MEDICAUX[mi];
    for (var mj = 0; mj < item.noms.length; mj++) {
      MOTS_PATHOLOGIES_DIRECTS[item.noms[mj]] = item.cle;
    }
  }

  function estMaladieDirecte(question) {
    var q = sansAccents(question.replace(/'/g, ' ').replace(/-/g, ' ')).trim();
    // Si la question est très courte (1-3 mots) et correspond à un nom de pathologie
    var mots = q.split(' ').filter(function(m) { return m.length > 0; });
    if (mots.length > 4) return null; // trop long pour une question directe

    // Vérifier si tous les mots correspondent à une pathologie
    for (var cle in MOTS_PATHOLOGIES_DIRECTS) {
      if (q === cle || q.indexOf(cle) >= 0) {
        // Vérifier que ce n'est pas une question d'identité ou autre
        if (!estIdentite(question)) {
          return MOTS_PATHOLOGIES_DIRECTS[cle];
        }
      }
    }
    return null;
  }

  function estIdentite(question) {
    var q = sansAccents(question);
    for (var i = 0; i < PATTERNS_IDENTITE.length; i++)
      if (q.indexOf(sansAccents(PATTERNS_IDENTITE[i])) >= 0) return true;
    return false;
  }

  // ── Phase 3 : Split des questions multiples ──
  function scinderQuestion(question) {
    // Détecter « et », « puis », « , » comme séparateurs de questions multiples
    var q = question.trim();
    var separateurs = [
      /\s+et\s+/gi,
      /\s+puis\s+/gi,
      /\s*,\s*/g,
      /\s+ainsi que\s+/gi,
    ];
    var parties = [q];
    for (var si = 0; si < separateurs.length; si++) {
      var nouvelles = [];
      for (var pj = 0; pj < parties.length; pj++) {
        var split = parties[pj].split(separateurs[si]);
        for (var sk = 0; sk < split.length; sk++) {
          var trimmed = split[sk].trim();
          if (trimmed.length > 0) nouvelles.push(trimmed);
        }
      }
      if (nouvelles.length > 1) parties = nouvelles;
    }
    return parties.length > 1 ? parties : null;
  }

  var SEUIL_RESONANCE_FAIT = 0.60; // seuil ÉLEVÉ : seuls les concepts quasi-exacts passent

  function motsDe(question) {
    // tokenisation simple : mots de 3+ lettres, sans accents
    var q = question.toLowerCase().replace(/[éèêë]/g, 'e').replace(/[àâä]/g, 'a')
      .replace(/[îï]/g, 'i').replace(/[ôö]/g, 'o').replace(/[ùûü]/g, 'u').replace(/ç/g, 'c');
    return q.match(/[a-zœ]{3,}/g) || [];
  }

  function sansAccents(s) {
    if (!s) return '';
    return s.toLowerCase().trim().replace(/\s+/g, ' ')
      .replace(/[éèêë]/g, 'e').replace(/[àâä]/g, 'a')
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
    // Phase 3 : Détection de questions multiples
    var parties = scinderQuestion(question);
    if (parties && parties.length > 1) {
      // Traiter la première question (la plus importante pour l'utilisateur)
      // Les questions multiples sont complexes à gérer — on prend la première
      // et on mentionne la multi-détection
      var premiere = parties[0];
      var core = repondreSimple(premiere);
      if (core.type !== 'REFUS') {
        var suite = ' (note : j\'ai détecté plusieurs questions dans votre message. Je réponds à la première — n\'hésitez pas à les poser une par une.)';
        if (core.type === 'IDENTITE') core.valeur = core.valeur || REPONSES_IDENTITE[0];
        return core;
      }
    }
    return repondreSimple(question);
  }

  function repondreSimple(question) {
    // Routage : IDENTITÉ → FAQ → CONDUITE → MÉDICAL → MALADIE DIRECTE → CALCUL → FAIT → RÉSONANCE → REFUS
    if (estIdentite(question)) return { type: 'IDENTITE' };

    var faq = estQuestionFAQ(question);
    if (faq) return { type: 'FAQ', concept: faq, valeur: FAQ[faq] };

    var conduite = estQuestionConduite(question);
    if (conduite) return { type: 'CONDUITE', concept: conduite, valeur: CONDUITES_URGENCE[conduite] };

    var maladie = estQuestionMedicale(question);
    if (maladie) return { type: 'MEDICAL', concept: maladie, valeur: FAITS_MEDICAUX[maladie] };

    // Phase 3 : Détection directe d'un mot de pathologie
    var directe = estMaladieDirecte(question);
    if (directe) return { type: 'MEDICAL', concept: directe, valeur: FAITS_MEDICAUX[directe] };

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

  // ── Descriptions de concepts ──
  var DESCRIPTIONS_CONCEPTS = {
    'lumiere': 'La lumière est une onde électromagnétique. Dans le modèle harmonique, elle suit la même équation d\'onde que toutes les connaissances.',
    'amour': 'L\'amour est un concept fondamental qui, selon la Théorie Harmonique, possède une signature ondulatoire propre — comme toute émotion.',
    'musique': 'La musique est une organisation harmonique de fréquences. Elle est régie par les mêmes rapports que le nombre d\'or.',
    'eau': 'L\'eau est le solvant universel. Sa structure moléculaire en réseau de ponts hydrogène la rend sensible aux fréquences vibratoires.',
    'sante': 'La santé est un état d\'équilibre harmonique entre les 5 oscillateurs physiologiques (S/D, LF/HF, I/E, β/α, T°).',
    'chat': 'Le chat est un mammifère domestique de la famille des félidés.',
    'chien': 'Le chien est un mammifère domestique de la famille des canidés.',
    'oiseau': 'Les oiseaux sont des vertébrés tétrapodes ailés, de la classe des aves.',
    // +12 concepts (Phase 1)
    'temps': 'Le temps est une dimension fondamentale de la physique. Dans l\'équation harmonique Ψ = Σ H_n·(Ψ₁)ⁿ, le temps émerge de la phase des ondes.',
    'espace': 'L\'espace est le cadre tridimensionnel de notre univers. La Théorie Harmonique le décrit comme un champ d\'ondes stationnaires.',
    'liberte': 'La liberté est la capacité d\'agir selon sa propre volonté. Concept fondamental des droits humains, reconnu par la Déclaration universelle de 1948.',
    'justice': 'La justice est le principe moral qui vise à respecter les droits de chacun. Elle repose sur l\'équité, l\'impartialité et la proportionnalité.',
    'verite': 'La vérité est la correspondance entre ce qui est dit et ce qui est. Dans le système KA, elle est garantie par le déterminisme et l\'audit.',
    'nombre': 'Le nombre est une abstraction mathématique représentant une quantité. Les nombres entiers émergent des phases dans l\'encodeur harmonique.',
    'energie': 'L\'énergie est la capacité à produire un travail ou un transfert thermique. Dans le modèle harmonique, Ψ² représente la densité d\'énergie.',
    'force': 'La force est toute action mécanique capable de modifier le mouvement ou la forme d\'un corps. Elle se mesure en newtons (N).',
    'vie': 'La vie est un ensemble de phénomènes caractérisés par l\'organisation, le métabolisme, la croissance et la reproduction. Son origine est une question scientifique ouverte.',
    'mort': 'La mort est l\'arrêt irréversible des fonctions vitales d\'un organisme. Elle marque la fin de l\'entropie négative propre aux systèmes vivants.',
    'connaissance': 'La connaissance est l\'ensemble des informations comprises et intégrées. KA est un amplificateur de connaissance, pas un générateur.',
    'sagesse': 'La sagesse est la capacité à discerner ce qui est vrai et juste, et à agir en conséquence. Aristote disait : « La sagesse est la science des principes premiers. »',
  };

  // ── Réponses REFUS variées ──
  var REFUS_VARIES = [
    'Je ne peux pas répondre à ça. Je préfère me taire plutôt que d\'inventer.',
    'Désolé, cela dépasse le cadre de mes connaissances. Je ne réponds que sur ce que je sais avec certitude.',
    'Je n\'ai pas d\'information fiable sur ce sujet. Le noyau harmonique ne fabrique jamais de réponse.',
  ];

  // ── Balises de confiance ──
  var BALISES_CONFIANCE = {
    'IDENTITE': '🤖',
    'FAQ': '📚',
    'MEDICAL': '✅',
    'CONDUITE': '⚠️',
    'CALC': '🔢',
    'FAIT': '💡',
    'REFUS': '—',
  };

  function phraseModele(core) {
    var balise = BALISES_CONFIANCE[core.type] || '';

    if (core.type === 'IDENTITE') {
      var idx = Math.floor(Math.random() * REPONSES_IDENTITE.length);
      return REPONSES_IDENTITE[idx];
    }
    if (core.type === 'FAQ') return balise + ' ' + core.valeur;
    if (core.type === 'MEDICAL') return balise + ' ' + core.valeur;
    if (core.type === 'CONDUITE') return balise + ' ' + core.valeur;
    if (core.type === 'CALC') {
      var v = core.valeur;
      var s = (v === Math.floor(v)) ? String(v) : v.toFixed(6).replace(/0+$/, '').replace(/\.$/, '');
      return balise + ' Le résultat est ' + s + '. Calculé par les ondes.';
    }
    if (core.type === 'FAIT') {
      var desc = DESCRIPTIONS_CONCEPTS[sansAccents(core.concept)];
      if (desc) return balise + ' ' + desc;
      return balise + ' Oui, je connais ' + core.concept + '.';
    }
    return REFUS_VARIES[Math.floor(Math.random() * REFUS_VARIES.length)];
  }

  // ═══════════════ VOCALISATION TTS — texte écrit → texte PARLÉ ═══════════════
  // Port exact de vocaliser() (pont_hybride.py). Le synthétiseur (Piper /
  // Web Speech) lit mal les symboles réels du corpus (≥, →, %, ⚠️, —, g/L,
  // 140/90…). Le CONTENU reste identique, seuls les symboles deviennent des
  // mots. Utilisé par ka_index.html avant la synthèse vocale.
  var UNITES_VOCALES = [
    ['mmol/L', ' millimoles par litre'], ['mg/dL', ' milligrammes par décilitre'],
    ['mg/dl', ' milligrammes par décilitre'], ['mg/kg', ' milligrammes par kilogramme'],
    ['g/L', ' grammes par litre'], ['mmHg', ' millimètres de mercure'],
    ['HbA1c', ' hémoglobine glyquée'], ['ml/kg', ' millilitres par kilogramme'],
    ['ml', ' millilitres'], ['mg', ' milligrammes'], ['kg', ' kilogrammes'],
    ['cm', ' centimètres'], ['°C', ' degrés'], ['°', ' degrés']];

  var FREQUENCES_VOCALES = [
    ['/min', ' par minute'], ['/j', ' par jour'], ['/an', ' par an'],
    ['/h', ' par heure'], ['/kg', ' par kilogramme'], ['/semaine', ' par semaine'],
    ['/mois', ' par mois']];

  function vocaliser(texte) {
    if (!texte) return texte;
    var t = String(texte);
    // 1. Unités et termes médicaux (ils contiennent /, °, %… → AVANT)
    UNITES_VOCALES.forEach(function (p) { t = t.split(p[0]).join(p[1]); });
    // 2. Flèches, tirets longs, comparaisons, pourcentages
    t = t.split('→').join(', ').split('—').join(', ').split('–').join(', ');
    t = t.split('≥').join('supérieur ou égal à').split('≤').join('inférieur ou égal à');
    t = t.split('≈').join('environ').split('±').join('environ');
    t = t.split('%').join(' pour cent').split('&').join(' et ').split('=').join(' égale ');
    // 3. « 24h/24 » → « 24 heures sur 24 » ; « 7j/7 » → « 7 jours sur 7 » ;
    //    « 140/90 » → « 140 sur 90 » ; « 6h » → « 6 heures »
    t = t.replace(/(\d+)h\/(\d+)/g, '$1 heures sur $2');
    t = t.replace(/(\d+)j\/(\d+)/g, '$1 jours sur $2');
    t = t.replace(/(\d+)\/(\d+)/g, '$1 sur $2');
    t = t.replace(/(\d+)h\b/g, '$1 heures');
    t = t.replace(/(\d+)j\b/g, '$1 jours');
    // 4. « 2x/j » → « 2 fois par jour » (AVANT les fréquences)
    t = t.replace(/(\d+)\s*x\s*\/\s*j/g, '$1 fois par jour');
    FREQUENCES_VOCALES.forEach(function (p) { t = t.split(p[0]).join(p[1]); });
    t = t.split('/').join(' par ');
    // 5. Intervalles et opérateurs : « 40-60 » → « de 40 à 60 », « > » → « plus de »
    t = t.replace(/(\d+)\s*-\s*(\d+)/g, 'de $1 à $2');
    t = t.split('>').join(' plus de ').split('<').join(' moins de ');
    t = t.split('×').join(' fois ').split('÷').join(' divisé par ').split('+').join(' plus ');
    // 6. Parenthèses → virgules (contenu conservé : précision médicale)
    t = t.replace(/\(/g, ', ').replace(/\)/g, '');
    // 7. Markdown et émojis (plages Unicode des symboles décoratifs)
    t = t.replace(/\*\*/g, '').replace(/`/g, '').replace(/#/g, '');
    t = t.replace(/[\u2190-\u21FF\u2600-\u27BF\uFE0F\ud800-\udfff]/g, '');
    // 8. Nettoyage : doubles espaces, virgules orphelines
    t = t.replace(/\s{2,}/g, ' ').replace(/\s+,/g, ',').replace(/,\s*,/g, ',');
    return t.trim();
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
    if (core.type === 'FAIT' || core.type === 'FAQ') return phrase.indexOf(core.concept.toLowerCase()) >= 0;
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
  ['chat', 'chien', 'oiseau', 'lumière', 'amour', 'eau', 'musique', 'santé',
   'temps', 'espace', 'liberté', 'justice', 'vérité', 'nombre', 'énergie', 'force',
   'vie', 'mort', 'connaissance', 'sagesse'].forEach(apprendre);

  var stats = { CALC: 0, FAIT: 0, REFUS: 0, local: 0, serveur: 0, auditKO: 0,
                MEDICAL: 0, CONDUITE: 0, IDENTITE: 0, FAQ: 0 };

  function traiter(question, opts) {
    opts = opts || {};
    // Sauvegarder l'historique
    history.push({ question: question, timestamp: Date.now() });
    if (history.length > 5) history.shift();

    var core = repondre(question);
    if (stats[core.type] !== undefined) stats[core.type]++;
    else stats[core.type] = 0;

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
    return { concepts: Object.keys(concepts), seuil: SEUIL_RESONANCE, stats: stats, historySize: history.length };
  }

  function getHistory() { return history.slice(); }
  function clearHistory() { history = []; }

  global.KAHybrid = { traiter: traiter, etat: etat, calculer: calculer,
                      repondre: repondre, phraseModele: phraseModele,
                      vocaliser: vocaliser, getHistory: getHistory, clearHistory: clearHistory };
})(window);