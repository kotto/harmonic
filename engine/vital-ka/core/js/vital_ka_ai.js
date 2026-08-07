/**
 * Vital Ka AI — Assistant Médical Harmonique
 * ===========================================
 * Interface conversationnelle qui explique les diagnostics,
 * pose des questions de clarification, et raisonne sur
 * l'hologramme de sante du patient.
 * 
 * Fonctionne en 2 modes :
 *   - LOCAL  : 100% templates deterministes (hors-ligne)
 *   - HYBRID : Templates + LLM style polishing (si serveur dispo)
 * 
 * Usage :
 *   const ai = new KACareAI();
 *   ai.explain(diagnosisResult, hologram);
 *   ai.askClarifyingQuestion(differentials);
 *   ai.reason(symptoms, knowledge);
 */

class KACareAI {
  /**
   * Spécialisations médicales — orientent l'explication, la recherche
   * et les questions de clarification. Le moteur de diagnostic
   * (cosineSim) reste inchangé : zéro hallucination.
   * base = clé Knowledge à booster, diseases = pathologies du domaine.
   */
  static SPECIALTIES = {
    generaliste: { icon: '🩺', label: 'Médecine générale', base: null, diseases: [], focus: 'vue d\'ensemble, orientation et prévention' },
    urgences:    { icon: '🚨', label: 'Urgences & Réanimation', base: 'urgences', diseases: ['Infarctus', 'AVC', 'Embolie_pulmonaire', 'Méningite', 'Septicémie', 'Appendicite', 'Allergie_sévère', 'Dengue_sévère', 'Paludisme_grave', 'Choléra', 'Diabète_décompensé', 'Fièvre_jaune', 'Trypanosomiase', 'Leishmaniose', 'Crise_asthme'], focus: 'tri, gravité et délais d\'action' },
    pediatrie:   { icon: '👶', label: 'Pédiatrie', base: 'pediatrie', diseases: ['Palu_enfant', 'Bronchite', 'Pneumonie', 'Gastro', 'Angine', 'Rhume', 'Méningite'], focus: 'posologies poids-adaptées, seuils de gravité pédiatriques' },
    mere_enfant: { icon: '🤰', label: 'Gynéco-Obstétrique', base: 'mere_enfant', diseases: ['Palu_femme_enceinte'], focus: 'grossesse, post-partum et nouveau-né' },
    infectio:    { icon: '🦠', label: 'Infectiologie & Tropical', base: 'ntd', diseases: ['Paludisme_simple', 'Paludisme_grave', 'Dengue', 'Dengue_sévère', 'Chikungunya', 'Choléra', 'Fièvre_jaune', 'Zika', 'Leptospirose', 'Bilharziose', 'Trypanosomiase', 'Leishmaniose', 'Onchocercose', 'Filariose', 'Typhoïde', 'COVID-19', 'Grippe', 'Palu_femme_enceinte', 'Palu_enfant'], focus: 'contexte épidémiologique, tests biologiques et protocoles tropicaux' },
    cardio:      { icon: '🫀', label: 'Cardiologie', base: null, diseases: ['Infarctus', 'Phlébite', 'Embolie_pulmonaire', 'Crise_angoisse'], focus: 'douleur thoracique, ECG et facteurs de risque cardiovasculaire' },
    pneumo:      { icon: '🫁', label: 'Pneumologie', base: null, diseases: ['Pneumonie', 'Bronchite', 'Crise_asthme', 'COVID-19', 'Embolie_pulmonaire'], focus: 'détresse respiratoire, SpO2 et auscultation' },
    psy:         { icon: '🧠', label: 'Santé mentale', base: 'sante_mentale', diseases: ['Dépression', 'Crise_angoisse'], focus: 'entretien clinique, échelles et orientation psychiatrique' },
    nutrition:   { icon: '🥗', label: 'Nutrition', base: 'malnutrition', diseases: [], focus: 'statut nutritionnel, MAC/MAM et renutrition' }
  };

  constructor() {
    this.mode = 'local'; // 'local' | 'hybrid'
    this.conversation = [];
    this.maxTurns = 10;
    this.specialty = 'generaliste';
    this._pendingClarification = null; // {question, disease, add}
  }

  /** Change la spécialisation active */
  setSpecialty(id) {
    if (KACareAI.SPECIALTIES[id]) this.specialty = id;
  }

  /** Retourne la config de la spécialité active */
  getSpecialty() {
    return KACareAI.SPECIALTIES[this.specialty] || KACareAI.SPECIALTIES.generaliste;
  }
  
  /**
   * Tente de se connecter au serveur harmonique
   */
  async init() {
    try {
      const resp = await fetch('http://localhost:8765/api/health', { signal: AbortSignal.timeout(2000) });
      if (resp.ok) this.mode = 'hybrid';
    } catch {
      this.mode = 'local';
    }
    return this.mode;
  }
  
	  /**
	   * Explique un diagnostic en langage naturel
	   * @param {Object} top - Meilleur diagnostic {name, score, g, u, c, d}
	   * @param {Object} holo - Hologramme du patient
	   * @param {Object} [patientVector] - Vecteur patient pour résonance phyto
	   * @returns {string} Explication en francais
	   */
	  explain(top, holo, patientVector) {
    const score = top.score || 0;
    const name = top.name || 'inconnue';
    const gravity = top.g || 'MODEREE';
    const urgent = top.u || false;
    const advice = top.c || '';
    const delay = top.d || '';
    
    let explanation = '';
    
    // Niveau de confiance
    if (score > 0.8) {
      explanation += `🔬 **Haute resonance** (${(score*100).toFixed(0)}%) avec **${name}**.\n\n`;
      explanation += `Les symptomes presentes correspondent fortement a la signature harmonique de cette pathologie. `;
    } else if (score > 0.5) {
      explanation += `📊 **Resonance significative** (${(score*100).toFixed(0)}%) avec **${name}**.\n\n`;
      explanation += `Plusieurs symptomes concordent, mais certains signes cles sont absents ou divergents. Un examen complementaire est recommande. `;
    } else if (score > 0.3) {
      explanation += `🔍 **Resonance moderee** (${(score*100).toFixed(0)}%) avec **${name}**.\n\n`;
      explanation += `Quelques symptomes correspondent, mais la signature est incomplete. Cette possibilite ne peut etre exclue sans investigation supplementaire. `;
    } else {
      explanation += `❓ **Resonance faible** (${(score*100).toFixed(0)}%). Aucune pathologie ne correspond clairement aux symptomes decrits.\n\n`;
      explanation += `Il est possible que les symptomes soient atypiques, incomplets, ou relevant d'une pathologie non referencee dans la base. `;
    }
    
    // Gravité
    if (urgent) {
      explanation += `\n\n🚨 **URGENCE VITALE** — ${name} est une urgence medicale. Gravit e : ${gravity}. Delai recommande : ${delay}.`;
    } else {
      explanation += `\n\nGravite : ${gravity}. Delai de consultation recommande : ${delay}.`;
    }
    
    // Conduite
    if (advice) {
      explanation += `\n\n▶ **Conduite a tenir :** ${advice}`;
    }

    // Lecture spécialisée
    if (this.specialty !== 'generaliste') {
      const spec = this.getSpecialty();
      const inDomain = spec.diseases.includes(name);
      explanation += `\n\n${spec.icon} **${spec.label}** : `;
      explanation += inDomain
        ? `Pathologie au coeur de cette specialite — ${spec.focus}.`
        : `Hors domaine principal — lecture orientee : ${spec.focus}.`;
    }

	    // Hologramme insight
	    if (holo && holo.features) {
	      const nFeatures = holo.features.length;
	      explanation += `\n\n🧬 **Hologramme :** ${nFeatures} caracteristiques encodees.`;
	    }

	    // ── Phytothérapie complémentaire ──
	    if (typeof Knowledge === 'object' && Knowledge && Knowledge.getPhytoFor && top.name) {
	      try {
	        const plants = Knowledge.getPhytoFor([top.name], patientVector || null);
	        if (plants && plants.length) {
	          explanation += '\n\n---\n\n🌿 **Phytothérapie traditionnelle associée**\n\n';
	          const ab = plants.filter(p => p.grade_evidence === 'A' || p.grade_evidence === 'B');
	          const cPlants = plants.filter(p => p.grade_evidence === 'C' && p.niveau_recommandation !== 'vigilance');
	          const vigPlants = plants.filter(p => p.niveau_recommandation === 'vigilance');
	          if (ab.length) {
	            explanation += '**Plantes documentées (Grade A/B) :**\n';
	            for (const p of ab.slice(0, 4)) {
	              const local = (p.noms_locaux && p.noms_locaux.length) ? ' (' + p.noms_locaux[0] + ')' : '';
	              explanation += `- 🌿 **${p.nom_scientifique}**${local} — Grade ${p.grade_evidence} — ${p.partie_utilisee} · ${p.preparation}\n`;
	            }
	          }
	          if (cPlants.length) {
	            explanation += `\n*${cPlants.length} plante(s) supplémentaire(s) d'usage traditionnel (Grade C).*\n`;
	          }
	          if (vigPlants.length) {
	            explanation += `\n⚠️ **${vigPlants.length} plante(s) toxique(s) à éviter :**\n`;
	            for (const p of vigPlants.slice(0, 3)) {
	              explanation += `- ⛔ ${p.nom_scientifique} — ${p.precautions || 'Toxique'}\n`;
	            }
	          }
	          explanation += '\n*La phytothérapie ne remplace pas le traitement de référence.*';
	        }
	      } catch (e) { /* silencieux */ }
	    }
    
    return explanation;
  }
  
  /**
   * Genere une question de clarification pour affiner le diagnostic
   * @param {Array} differentials - Diagnostics differentiels [{name, score, ...}]
   * @param {Array} askedQuestions - Questions deja posees
   * @returns {string|null} Question ou null si assez d'info
   */
  askClarifyingQuestion(differentials, askedQuestions = []) {
    if (differentials.length < 2) return null;
    if (askedQuestions.length >= 5) return null;

    const top = differentials[0];
    const second = differentials[1];
    const gap = top.score - second.score;

    // Si l'ecart est grand, pas besoin de clarifier
    if (gap > 0.25) return null;

    // Questions discriminantes : q = question, add = symptome DB injecte si "oui"
    // (cle symptomMap avec underscores — matchee comme token unique par encodeSympt)
    const questions = {
      'COVID-19': [{ q: 'Avez-vous perdu l\'odorat (anosmie) ou le gout (agueusie) ?', add: 'anosmie' }, { q: 'La fievre est-elle superieure a 38.5°C ?', add: 'fièvre_élevée' }],
      'Grippe': [{ q: 'Les courbatures sont-elles intenses ?', add: 'courbatures' }, { q: 'Le debut a-t-il ete brutal (en quelques heures) ?', add: 'fièvre_brutale' }],
      'Paludisme_simple': [{ q: 'La fievre est-elle cyclique (pics toutes les 48h) ?', add: 'fièvre_cyclique' }, { q: 'Avez-vous voyage en zone tropicale recemment ?', add: null }],
      'Dengue': [{ q: 'Avez-vous des douleurs derriere les yeux (retro-orbitaires) ?', add: 'douleurs_rétro_orbitaires' }, { q: 'Avez-vous une eruption cutanee ?', add: 'éruption_cutanée' }],
      'Bronchite': [{ q: 'La toux est-elle grasse (avec expectorations) ?', add: 'toux_grasse' }, { q: 'Avez-vous de la fievre ?', add: 'fièvre' }],
      'Pneumonie': [{ q: 'Les expectorations sont-elles colorees (jaunes/vertes) ?', add: 'expectorations_colorées' }, { q: 'La respiration est-elle rapide ou difficile ?', add: 'respiration_rapide' }],
      'Angine': [{ q: 'Avez-vous mal a la gorge au point de ne pas pouvoir avaler ?', add: 'difficulté_avaler' }, { q: 'Avez-vous des ganglions dans le cou ?', add: 'ganglions' }],
      'Gastro': [{ q: 'Les vomissements sont-ils frequents ?', add: 'vomissements' }, { q: 'Y a-t-il du sang dans les selles ?', add: 'diarrhée_sanglante' }],
      'Infection_urinaire': [{ q: 'Ressentez-vous des brulures en urinant ?', add: 'brûlures_urinaires' }, { q: 'Les urines sont-elles troubles ou foncees ?', add: 'urines_troubles' }],
      'Migraine': [{ q: 'La douleur est-elle d\'un seul cote de la tete ?', add: 'maux_de_tête_intenses' }, { q: 'La lumiere ou le bruit aggravent-ils la douleur ?', add: 'photophobie' }],
      'Dengue_sévère': [{ q: 'Avez-vous des saignements (gencives, nez) ?', add: 'saignements' }, { q: 'La douleur abdominale est-elle intense ?', add: 'douleur_abdominale_intense' }],
      'Chikungunya': [{ q: 'Les douleurs articulaires sont-elles symetriques et intenses ?', add: 'douleurs_articulaires_intenses' }, { q: 'Avez-vous une eruption cutanee qui gratte ?', add: 'prurit' }],
      'Choléra': [{ q: 'Les selles sont-elles liquides comme de l\'eau de riz ?', add: 'diarrhée_aqueuse_profuse' }, { q: 'Avez-vous soif intense ?', add: 'soif_intense' }],
      'Leptospirose': [{ q: 'Avez-vous ete en contact avec de l\'eau douce (riviere, lac) ?', add: null }, { q: 'Les mollets sont-ils douloureux ?', add: 'myalgies_mollets' }],
      'Typhoïde': [{ q: 'La fievre augmente-t-elle progressivement chaque jour ?', add: 'fièvre_progressive' }, { q: 'Avez-vous des taches roses sur l\'abdomen ?', add: 'taches_roses' }]
    };

    // Trouver la meilleure question discriminante
    const candidates = [];
    for (const d of differentials.slice(0, 3)) {
      const qs = questions[d.name] || [];
      qs.forEach(item => {
        if (!askedQuestions.includes(item.q)) {
          candidates.push({ q: item.q, add: item.add, disease: d.name, score: d.score });
        }
      });
    }

    if (candidates.length === 0) {
      const generic = 'Y a-t-il d\'autres symptomes que vous n\'avez pas mentionnes ?';
      if (askedQuestions.includes(generic)) return null;
      this._pendingClarification = { question: generic, disease: null, add: null };
      return generic;
    }

    // Priorite aux questions du domaine de la specialite, puis au score
    const spec = this.getSpecialty();
    candidates.sort((a, b) => {
      const ba = spec.diseases.includes(a.disease) ? 1 : 0;
      const bb = spec.diseases.includes(b.disease) ? 1 : 0;
      return (bb - ba) || (b.score - a.score);
    });

    const chosen = candidates[0];
    this._pendingClarification = { question: chosen.q, disease: chosen.disease, add: chosen.add };
    return chosen.q;
  }

  /**
   * Integre la reponse a une question de clarification dans les symptomes.
   * @param {string} answer - Reponse de l'utilisateur (oui/non ou texte libre)
   * @param {string} symptomsText - Texte actuel du champ symptomes
   * @returns {{text: string, integrated: boolean}} Nouveau texte + indicateur
   */
  integrateClarification(answer, symptomsText) {
    const p = this._pendingClarification;
    this._pendingClarification = null;
    if (!p) return { text: symptomsText, integrated: false };

    const a = answer.trim();
    const isYes = /^(oui|ouais|yes|yep|oe|ok|exactement|tout a fait|vrai)\b/i.test(a);
    const isNo = /^(non|no|nan|pas du tout)\b/i.test(a);

    // Reponse binaire avec symptome cible
    if (p.add && (isYes || isNo)) {
      if (!isYes) return { text: symptomsText, integrated: true };
      const base = symptomsText ? symptomsText.replace(/[,\s]+$/, '') + ', ' : '';
      return { text: base + p.add, integrated: true };
    }
    // Reponse binaire sans symptome cible (contexte) — rien a injecter
    if (isYes || isNo) return { text: symptomsText, integrated: true };
    // Reponse libre — ajouter le texte tel quel
    const base = symptomsText ? symptomsText.replace(/[,\s]+$/, '') + ', ' : '';
    return { text: base + a, integrated: true };
  }
  
  /**
   * Raisonnement harmonique complet
   * @param {Array} scores - Tous les diagnostics tries par score
   * @param {Object} holo - Hologramme patient
   * @returns {string} Analyse detaillee
   */
  reason(scores, holo) {
    let reasoning = '';
    const top = scores[0];
    
    reasoning += `## 🧠 Raisonnement Harmonique\n\n`;
    reasoning += `**Hypothese principale :** ${top.name} (${(top.score*100).toFixed(0)}%)\n`;
    reasoning += `**Gravite :** ${top.g}\n\n`;
    
    // Expliquer pourquoi
    reasoning += `### Pourquoi ${top.name} ?\n`;
    reasoning += `La signature harmonique de ${top.name} presente la plus forte coherence ondulatoire avec les symptomes du patient. `;
    reasoning += `Dans l'espace vectoriel C⁵¹², le cosinus entre le vecteur patient et le vecteur ${top.name} est de ${top.score.toFixed(3)}.\n\n`;
    
    // Diagnostics differentiels
    if (scores.length > 1) {
      reasoning += `### Diagnostics differentiels\n`;
      const diffs = scores.slice(1, 4);
      diffs.forEach((d, i) => {
        const gap = top.score - d.score;
        reasoning += `${i+1}. **${d.name}** — ${(d.score*100).toFixed(0)}% (ecart : ${(gap*100).toFixed(0)} pts)\n`;
        if (gap < 0.1) {
          reasoning += `   ⚠️ Proche — a considerer serieusement.\n`;
        }
      });
    }
    
    // Recommandation
    reasoning += `\n### Recommandation\n`;
    if (top.u && top.score > 0.5) {
      reasoning += `🚨 **Urgence confirmee.** ${top.c}\n`;
    } else if (top.score > 0.7) {
      reasoning += `✅ Diagnostic probable. ${top.c}\n`;
    } else {
      reasoning += `🔍 Diagnostic incertain. Investigations complementaires recommandees.\n`;
    }
    
    // Hologramme
    if (holo) {
      reasoning += `\n### Hologramme patient\n`;
      reasoning += Hologram.explain(holo);
    }
    
    return reasoning;
  }
  
  /**
   * Mode epidemie : detecte des clusters de patients similaires
   * @param {Array} patients - Liste d'hologrammes patients
   * @param {number} threshold - Seuil de similarite (0-1)
   * @returns {Array} Clusters detectes
   */
  detectClusters(patients, threshold = 0.7) {
    const clusters = [];
    const assigned = new Set();
    
    for (let i = 0; i < patients.length; i++) {
      if (assigned.has(i)) continue;
      
      const cluster = { members: [i], centroid: patients[i].holo, size: 1 };
      
      for (let j = i + 1; j < patients.length; j++) {
        if (assigned.has(j)) continue;
        const sim = Hologram.cosineSim(patients[i].holo, patients[j].holo);
        if (sim >= threshold) {
          cluster.members.push(j);
          cluster.size++;
          assigned.add(j);
        }
      }
      
      if (cluster.size >= 3) {
        cluster.alert = `⚠️ Cluster de ${cluster.size} patients similaires detecte`;
        clusters.push(cluster);
      }
      assigned.add(i);
    }
    
    return clusters;
  }
  
  /**
   * Trie les resultats Knowledge en boostant la base de la specialite active
   * @param {Array} results - Resultats de Knowledge.search()
   * @returns {Array} Resultats retries (copie)
   */
  _boostBySpecialty(results) {
    const spec = this.getSpecialty();
    if (!spec.base || !results || !results.length) return results;
    return results.slice().sort((a, b) => {
      const ba = a.base === spec.base ? 1 : 0;
      const bb = b.base === spec.base ? 1 : 0;
      return (bb - ba) || ((b.score || 0) - (a.score || 0));
    });
  }

  /**
   * Recherche médicale avancée (médicaments, protocoles, malnutrition)
   * @param {string} query
   * @returns {string} Réponse formatée
   */
  async searchMedical(query) {
    // S'assurer que Knowledge est chargé
    if (typeof Knowledge !== 'undefined') {
      await Knowledge.init();
    }
    
    const q = query.toLowerCase();
    
    // Détecter le type de question
    if (q.includes('médicament') || q.includes('traitement') || q.includes('dose') || q.includes('posologie') || q.includes('quoi donner')) {
      // Recherche médicament
      const drugName = q.replace(/médicament|traitement|dose|posologie|quoi donner|pour |contre |comment traiter/gi, '').trim();
      const drug = Knowledge.getDrug(drugName);
      if (drug) {
        return Knowledge.formatDrug(drug);
      }
      // Recherche générale
      const results = this._boostBySpecialty(Knowledge.search(drugName));
      if (results.length > 0) {
        const r = results[0];
        return r.type === 'médicament' ? Knowledge.formatDrug(r.data) : Knowledge.formatProtocol(r.data);
      }
    }
    
    if (q.includes('grossesse') || q.includes('accouchement') || q.includes('enceinte') || q.includes('postpartum') || q.includes('bébé') || q.includes('nouveau') || q.includes('allaitement')) {
      const results = this._boostBySpecialty(Knowledge.search(q));
      if (results.length > 0) {
        return Knowledge.formatProtocol(results[0].data);
      }
    }
    
    if (q.includes('malnutri') || q.includes('maigre') || q.includes('poids') || q.includes('muac') || q.includes('oedème') || q.includes('kwashiorkor') || q.includes('marasme')) {
      const results = this._boostBySpecialty(Knowledge.search(q));
      if (results.length > 0) {
        return Knowledge.formatProtocol(results[0].data);
      }
    }
    
    // Fallback : recherche générale
    if (typeof Knowledge !== 'undefined') {
      const results = this._boostBySpecialty(Knowledge.search(q));
      if (results.length > 0) {
        return results.slice(0, 3).map(r => 
          r.type === 'médicament' ? `💊 ${r.data.nom}` : `🏥 ${r.data.nom}`
        ).join('\n') + '\n\nDemandez une fiche spécifique pour plus de détails.';
      }
    }
    
    // Fallback ultime : connaissance intégrée
    return this.searchKnowledge(q);
  }
  
  /**
   * Recherche dans la base intégrée (fallback minimal)
   */
  searchKnowledge(query) {
    const kb = {
      paludisme: 'CTA (Artemether+Lumefantrine) 3j. Prevention: moustiquaire impregnee.',
      dengue: 'Paracetamol UNIQUEMENT (pas AINS). Hydratation.',
      cholera: 'SRO ou Ringer Lactate IV. Doxycycline.',
      meningite: 'URGENCE. Antibiotiques IV immediats. Ponction lombaire.',
      infarctus: 'URGENCE VITALE. Appeler le 15. Aspirine 300mg a macher.',
      hypertension: 'HTA >140/90. Reduction sel, perte poids. IEC ou ARA2.',
      diabete: 'HbA1c cible <7%. Metformine 500-2000mg/j.',
      infection_urinaire: 'Amoxicilline ou Ciprofloxacine. Boire abondamment.',
      pneumonie: 'Amoxicilline 1g/8h x7j. Si severe: Ceftriaxone IV.',
      asthme: 'Salbutamol en crise. Corticoides inhales en fond.'
    };
    const q = query.toLowerCase();
    for (const [key, answer] of Object.entries(kb)) {
      if (q.includes(key)) return answer;
    }
    return `Aucune connaissance specifique trouvee. Essayez "medicament [nom]" ou "protocole [condition]" pour une recherche precise.`;
  }
  
  /**
   * Mode formation : explique le raisonnement pas a pas
   * @param {Object} top - Meilleur diagnostic
   * @param {Object} holo - Hologramme
   * @returns {string} Explication pedagogique
   */
  teach(top, holo) {
    let lesson = '';
    lesson += `## 📚 Comprendre le diagnostic de ${top.name}\n\n`;
    lesson += `### Etape 1 : Capture des symptomes\n`;
    lesson += `Chaque symptome est transforme en une **onde** dans l'espace harmonique C⁵¹². `;
    lesson += `Les mots comme "fievre", "toux", "douleur" sont encodes en angles via la fonction de hachage FNV-1a, `;
    lesson += `puis projetes sur le cercle unitaire complexe. La position de chaque symptome est espacée selon le nombre d'or φ (1.618...).\n\n`;
    
    lesson += `### Etape 2 : Construction de la signature maladie\n`;
    lesson += `${top.name} possede une signature pre-calculee : la somme des ondes de ses symptomes caracteristiques. `;
    lesson += `Ces signatures sont stockees dans la base de connaissances (41 pathologies).\n\n`;
    
    lesson += `### Etape 3 : Mesure de resonance\n`;
    lesson += `On calcule le **cosinus** entre le vecteur du patient et chaque vecteur maladie. `;
    lesson += `Un cosinus de 1.0 = alignement parfait. Un cosinus de 0.0 = aucune relation.\n`;
    lesson += `Score ${top.name} : **${(top.score*100).toFixed(0)}%** = cosinus de ${top.score.toFixed(3)}\n\n`;
    
    lesson += `### Etape 4 : Classement\n`;
    lesson += `Les maladies sont classees par score decroissant. La premiere est le diagnostic principal. `;
    lesson += `Les suivantes constituent les diagnostics differentiels.\n\n`;
    
    lesson += `### Pourquoi zero hallucination ?\n`;
    lesson += `Contrairement a une IA generative qui "invente" le mot suivant, notre systeme mesure une propriete `;
    lesson += `mathematique reelle : la coherence ondulatoire entre deux vecteurs. Il n'y a rien a inventer — `;
    lesson += `le resultat est entierement determine par les symptomes fournis.`;
    
    return lesson;
  }
}

// Export global
if (typeof window !== 'undefined') {
  window.KACareAI = KACareAI;
}
