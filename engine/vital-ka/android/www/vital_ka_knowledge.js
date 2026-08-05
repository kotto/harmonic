/**
 * Vital Ka Knowledge — Base de connaissances médicales unifiée
 * =============================================================
 * Charge et interroge les bases de connaissances :
 *   - Médicaments essentiels (50)
 *   - Protocoles mère-enfant (10 conditions)
 *   - Protocoles malnutrition (5 conditions)
 *   - Maladies infectieuses (41 — déjà dans ka_core.js)
 * 
 * Usage :
 *   await Knowledge.init();
 *   const fiche = Knowledge.getDrug("paracetamol");
 *   const proto = Knowledge.getProtocol("pre_eclampsie");
 *   const result = Knowledge.search("médicament fièvre grossesse");
 */

const Knowledge = {
  _loaded: false,
  _drugs: {},
  _mereEnfant: {},
  _malnutrition: {},
  _vihTb: {},
  _chroniques: {},
  _pediatrie: {},
  _urgences: {},
  _vaccination: {},
  _ntd: {},
  _santeMentale: {},
  
  /**
   * Charge toutes les bases de connaissances
   *
   * IMPORTANT : on utilise Promise.allSettled (et non Promise.all).
   * Avec Promise.all, l'échec d'UN SEUL fetch sur 11 rejette la promesse
   * globale → catch → _initMinimal() qui NE CONTIENT AUCUNE PLANTE.
   * Symptôme observé : "les plantes n'apparaissent pas" (le diagnostic, lui,
   * marche car ka_core.js a sa propre DB en dur chargée via Promise.allSettled).
   * Avec allSettled, chaque base est chargée indépendamment — la phyto reste
   * disponible même si p.ex. la vaccination échoue.
   */
  async init() {
    if (this._loaded) return;

    const results = await Promise.allSettled([
      fetch('data/vital_ka_pharmacie.json').then(r => r.json()),
      fetch('data/vital_ka_mere_enfant.json').then(r => r.json()),
      fetch('data/vital_ka_malnutrition.json').then(r => r.json()),
      fetch('data/vital_ka_vih_tb.json').then(r => r.json()),
      fetch('data/vital_ka_chroniques.json').then(r => r.json()),
      fetch('data/vital_ka_pediatrie.json').then(r => r.json()),
      fetch('data/vital_ka_urgences.json').then(r => r.json()),
      fetch('data/vital_ka_vaccination.json').then(r => r.json()),
      fetch('data/vital_ka_ntd.json').then(r => r.json()),
      fetch('data/vital_ka_sante_mentale.json').then(r => r.json()),
      fetch('data/vital_ka_phytotherapie.json').then(r => r.json()),
    ]);
    const val = (i, fb) => (results[i].status === 'fulfilled') ? results[i].value : fb;
    const failed = results.filter(r => r.status === 'rejected').length;
    if (failed === results.length) {
      // Tout a échoué → set minimal (offline complet sans fichiers data/)
      console.warn('[Knowledge] Aucune base chargée — set minimal embarqué');
      this._initMinimal();
      this._loaded = true;
      return;
    }
    if (failed > 0) {
      console.warn('[Knowledge] ' + failed + '/' + results.length + ' base(s) non chargée(s) — partial load');
    }

    const pharma = val(0, { medicaments: {} });
    const mere   = val(1, { conditions: {} });
    const mal    = val(2, { conditions: {} });
    const vih    = val(3, { conditions: {} });
    const chr    = val(4, { conditions: {} });
    const ped    = val(5, { conditions: {} });
    const urg    = val(6, { conditions: {} });
    const vacc   = val(7, { vaccins: {} });
    const ntd    = val(8, { conditions: {} });
    const psy    = val(9, { conditions: {} });
    const phyto  = val(10, {});

    this._drugs = pharma.medicaments || {};
    this._mereEnfant = mere.conditions || {};
    this._malnutrition = mal.conditions || {};
    this._vihTb = vih.conditions || {};
    this._chroniques = chr.conditions || {};
    this._pediatrie = ped.conditions || {};
    this._urgences = urg.conditions || {};
    this._vaccination = vacc.vaccins || {};
    this._ntd = ntd.conditions || {};
    this._santeMentale = psy.conditions || {};
    this._phyto = phyto.plantes || phyto || {};
    // Pré-calcul des vecteurs de plantes (résonance thérapeutique patient↔plante)
    this._plantVectors = {};
    for (const [key, plant] of Object.entries(this._phyto)) {
      if (plant && Array.isArray(plant.tokens_effet) && plant.tokens_effet.length) {
        if (typeof encodeSympt === 'function') {
          this._plantVectors[key] = encodeSympt(plant.tokens_effet.join(' '));
        }
      }
    }
    this._loaded = true;
  },
  
  /**
   * Initialisation minimale si les JSON ne sont pas accessibles
   */
  _initMinimal() {
    this._drugs = {
      paracetamol: { nom: "Paracétamol", dose_adulte: "500-1000mg / 6-8h (max 4g/j)", dose_enfant: "10-15mg/kg / 6h", grossesse: "OK", contre_indications: "Insuffisance hépatique sévère" },
      amoxicilline: { nom: "Amoxicilline", dose_adulte: "500mg-1g / 8h", dose_enfant: "25-50mg/kg/j en 2-3 prises", grossesse: "OK", contre_indications: "Allergie pénicillines" },
      sro: { nom: "SRO", dose_adulte: "200-400ml après chaque selle liquide", dose_enfant: "50-100ml par selle", preparation: "1 sachet dans 1L d'eau propre" },
      artemether_lumefantrine: { nom: "CTA (Coartem)", dose_adulte: "4 cp à H0, H8, H24, H36, H48, H60", dose_enfant: "Selon poids", attention: "Prendre avec repas gras" }
    };
    this._mereEnfant = {
      pre_eclampsie: { nom: "Pré-éclampsie", signes: ["HTA >140/90","protéinurie","œdème"], conduite: "Hospitalisation. Sulfate de Mg. Anti-hypertenseur si TA>160/110.", urgence: true },
      hemorragie_post_partum: { nom: "HPP", signes: ["saignement >500ml","utérus atone"], conduite: "Ocytocine 10UI IM. Masser utérus. Remplissage IV.", urgence: true }
    };
    this._malnutrition = {
      sam: { nom: "MAS", signes: ["MUAC <115mm","œdème pieds"], conduite: "Hospitalisation si complications. F-75 puis Plumpy'Nut.", urgence: true }
    };
  },
  
  /**
   * Recherche un médicament par nom
   */
  getDrug(name) {
    return this._drugs[name.toLowerCase().replace(/[^a-z0-9_]/g, '_')] || null;
  },
  
  /**
   * Recherche un protocole par condition
   */
  getProtocol(name) {
    return this._mereEnfant[name] || this._malnutrition[name] || this._vihTb[name] || this._chroniques[name] || this._pediatrie[name] || this._urgences[name] || this._ntd[name] || this._santeMentale[name] || null;
  },
  
  /**
   * Recherche un vaccin par nom
   */
  getVaccine(name) {
    return this._vaccination[name.toLowerCase().replace(/[^a-z0-9_]/g, '_')] || null;
  },
  
  /**
   * Phytothérapie complémentaire — retourne les plantes indiquées pour une liste
   * de clés de pathologies (noms DB). Si un vecteur patient est fourni, calcule
   * la RÉSONANCE THÉRAPEUTIQUE (cosineSim patient↔plante) et trie par
   * résonance pondérée par le grade (A=1.0, B=0.85, C=0.65).
   * Les plantes n'entrent JAMAIS dans le scoring diagnostique.
   * @param {string[]} indicationKeys — noms de pathologies
   * @param {Object} [patientVector] — vecteur patient (pVec de encodeSympt)
   * @returns {Array} plantes enrichies (_resonance, _resonanceScore ajoutés)
   */
  getPhytoFor(indicationKeys, patientVector) {
    if (!this._phyto) return [];
    const norm = s => String(s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]/g, '_');
    const wanted = new Set((indicationKeys || []).map(norm));
    const out = [];
    const hasCosSim = typeof cosineSim === 'function';
    for (const [key, p] of Object.entries(this._phyto)) {
      if (!p || !Array.isArray(p.indications)) continue;
      const matched = p.indications.filter(ind => wanted.has(norm(ind)));
      if (!matched.length) continue;
      const enriched = Object.assign({}, p, {
        indications_label: matched.join(', '),
        _key: key,
        _resonance: 0,
        _resonanceScore: 0
      });
      // Résonance thérapeutique : cosineSim(patient, plante_effets)
      if (patientVector && hasCosSim && this._plantVectors[key]) {
        const resonance = cosineSim(patientVector, this._plantVectors[key]);
        enriched._resonance = resonance;
        // Résonance pondérée : grade A=×1.0, B=×0.85, C=×0.65
        const gradeW = { A: 1.0, B: 0.85, C: 0.65 };
        enriched._resonanceScore = resonance * (gradeW[p.grade_evidence] || 0.5);
      }
      out.push(enriched);
    }
    // Tri : vigilance toujours en dernier ; sinon par résonance pondérée, sinon grade
    out.sort((a, b) => {
      const va = a.niveau_recommandation === 'vigilance' ? 3 : 0;
      const vb = b.niveau_recommandation === 'vigilance' ? 3 : 0;
      if (va !== vb) return va - vb;
      // Si résonance disponible, trier par score pondéré
      if (a._resonanceScore !== b._resonanceScore) return b._resonanceScore - a._resonanceScore;
      // Fallback : grade
      const gradeOrder = { A: 0, B: 1, C: 2 };
      const ga = gradeOrder[a.grade_evidence] ?? 2;
      const gb = gradeOrder[b.grade_evidence] ?? 2;
      if (ga !== gb) return ga - gb;
      return (a.nom_scientifique || '').localeCompare(b.nom_scientifique || '');
    });
    return out;
  },
  
  /**
   * Accès direct à une plante par clé
   */
  getPhyto(name) {
    if (!this._phyto) return null;
    return this._phyto[name] || this._phyto[name.toLowerCase().replace(/[^a-z0-9_]/g, '_')] || null;
  },
  
  /**
   * Recherche textuelle dans toutes les bases
   * @param {string} query
   * @returns {Array} Résultats triés par pertinence
   */
  search(query) {
    const q = query.toLowerCase();
    const results = [];
    
    // Chercher dans les médicaments
    for (const [key, drug] of Object.entries(this._drugs)) {
      const text = (drug.nom + ' ' + drug.classe + ' ' + (drug.indications || []).join(' ')).toLowerCase();
      if (text.includes(q) || q.split(' ').some(w => text.includes(w))) {
        results.push({ type: 'médicament', base: 'pharmacie', key, data: drug, score: this._score(q, text) });
      }
    }
    
    // Chercher dans mère-enfant
    for (const [key, cond] of Object.entries(this._mereEnfant)) {
      const text = (cond.nom + ' ' + (cond.signes || []).join(' ') + ' ' + (cond.conduite || '')).toLowerCase();
      if (text.includes(q) || q.split(' ').some(w => text.includes(w))) {
        results.push({ type: 'protocole', base: 'mere_enfant', key, data: cond, score: this._score(q, text) });
      }
    }
    
    // Chercher dans malnutrition
    for (const [key, cond] of Object.entries(this._malnutrition)) {
      const text = (cond.nom + ' ' + (cond.signes || []).join(' ') + ' ' + (cond.conduite || '')).toLowerCase();
      if (text.includes(q) || q.split(' ').some(w => text.includes(w))) {
        results.push({ type: 'protocole', base: 'malnutrition', key, data: cond, score: this._score(q, text) });
      }
    }
    
    // Chercher dans VIH/TB/MST
    for (const [key, cond] of Object.entries(this._vihTb)) {
      const signsText = (cond.signes || []).join(' ') || (cond.signes_indicateurs || []);
      const text = (cond.nom + ' ' + signsText + ' ' + (cond.conduite || '')).toLowerCase();
      if (text.includes(q) || q.split(' ').some(w => text.includes(w))) {
        results.push({ type: 'protocole', base: 'vih_tb', key, data: cond, score: this._score(q, text) });
      }
    }
    
    // Chercher dans chroniques
    for (const [key, cond] of Object.entries(this._chroniques)) {
      const text = (cond.nom + ' ' + (cond.signes || []).join(' ') + ' ' + (cond.definition || cond.conduite || '')).toLowerCase();
      if (text.includes(q) || q.split(' ').some(w => text.includes(w))) {
        results.push({ type: 'protocole', base: 'chroniques', key, data: cond, score: this._score(q, text) });
      }
    }
    
    // Chercher dans pédiatrie
    for (const [key, cond] of Object.entries(this._pediatrie)) {
      const text = (cond.nom + ' ' + (cond.signes || []).join(' ') + ' ' + (cond.conduite || cond.definition || '')).toLowerCase();
      if (text.includes(q) || q.split(' ').some(w => text.includes(w))) {
        results.push({ type: 'protocole', base: 'pediatrie', key, data: cond, score: this._score(q, text) });
      }
    }
    
    // Chercher dans urgences
    for (const [key, cond] of Object.entries(this._urgences)) {
      const text = (cond.nom + ' ' + (cond.signes || []).join(' ') + ' ' + (cond.conduite || '')).toLowerCase();
      if (text.includes(q) || q.split(' ').some(w => text.includes(w))) {
        results.push({ type: 'urgence', base: 'urgences', key, data: cond, score: this._score(q, text) });
      }
    }
    
    // Chercher dans NTDs
    for (const [key, cond] of Object.entries(this._ntd)) {
      const trText = typeof cond.traitement === 'string' ? cond.traitement : (cond.traitement ? JSON.stringify(cond.traitement) : '');
      const text = (cond.nom + ' ' + (cond.signes || []).join(' ') + ' ' + (cond.agent || '') + ' ' + trText).toLowerCase();
      if (text.includes(q) || q.split(' ').some(w => text.includes(w))) {
        results.push({ type: 'protocole', base: 'ntd', key, data: cond, score: this._score(q, text) });
      }
    }
    
    // Chercher dans santé mentale
    for (const [key, cond] of Object.entries(this._santeMentale)) {
      const text = (cond.nom + ' ' + (cond.signes || []).join(' ') + ' ' + (cond.conduite || '')).toLowerCase();
      if (text.includes(q) || q.split(' ').some(w => text.includes(w))) {
        results.push({ type: 'protocole', base: 'sante_mentale', key, data: cond, score: this._score(q, text) });
      }
    }
    
    // Chercher dans vaccination
    for (const [key, vacc] of Object.entries(this._vaccination)) {
      const text = (vacc.nom + ' ' + (vacc.maladie || '') + ' ' + (vacc.calendrier || '') + ' ' + (vacc.type || '')).toLowerCase();
      if (text.includes(q) || q.split(' ').some(w => text.includes(w))) {
        results.push({ type: 'vaccin', base: 'vaccination', key, data: vacc, score: this._score(q, text) });
      }
    }
    
    // Chercher dans phytothérapie
    if (this._phyto) {
      for (const [key, plant] of Object.entries(this._phyto)) {
        const text = ((plant.nom_scientifique || '') + ' ' + ((plant.noms_locaux || []).join(' ')) + ' ' + ((plant.indications || []).join(' ')) + ' ' + (plant.preparation || '')).toLowerCase();
        if (text.includes(q) || q.split(' ').some(w => text.includes(w))) {
          results.push({ type: 'phyto', base: 'phytotherapie', key, data: plant, score: this._score(q, text) });
        }
      }
    }
    
    results.sort((a, b) => b.score - a.score);
    return results.slice(0, 5);
  },
  
  _score(query, text) {
    const qWords = query.split(/\s+/);
    let score = 0;
    for (const w of qWords) {
      if (text.includes(w)) score += 1;
      if (text.startsWith(w)) score += 2;
    }
    return score / qWords.length;
  },
  
  /**
   * Formate une fiche médicament pour affichage
   */
  formatDrug(drug) {
    let f = `💊 **${drug.nom}** (${drug.classe})\n`;
    f += `📍 Voie: ${drug.voie}\n`;
    f += `👤 Adulte: ${drug.dose_adulte}\n`;
    if (drug.dose_enfant) f += `👶 Enfant: ${drug.dose_enfant}\n`;
    if (drug.grossesse) f += `🤰 Grossesse: ${drug.grossesse}\n`;
    if (drug.contre_indications) f += `🚫 CI: ${drug.contre_indications}\n`;
    if (drug.attention) f += `⚠️ ${drug.attention}\n`;
    if (drug.effets_secondaires) f += `📋 EI: ${drug.effets_secondaires}\n`;
    return f;
  },
  
  /**
   * Formate un protocole pour affichage
   */
  formatProtocol(cond) {
    let f = `🏥 **${cond.nom}**\n`;
    if (cond.signes) f += `🔍 Signes: ${Array.isArray(cond.signes) ? cond.signes.join(', ') : cond.signes}\n`;
    if (cond.conduite) f += `▶ Conduite: ${cond.conduite.substring(0, 300)}\n`;
    if (cond.urgence) f += `🚨 URGENCE\n`;
    if (cond.attention) f += `⚠️ ${cond.attention}\n`;
    return f;
  },
  
  /**
   * Vérifie les interactions médicamenteuses
   */
  checkInteraction(drug1, drug2) {
    const key1 = drug1.toLowerCase().replace(/[^a-z0-9_]/g, '_');
    const key2 = drug2.toLowerCase().replace(/[^a-z0-9_]/g, '_');
    const pair = `${key1}_${key2}`;
    const reverse = `${key2}_${key1}`;
    
    if (this._drugs.interactions) {
      return this._drugs.interactions[pair] || this._drugs.interactions[reverse] || null;
    }
    return null;
  }
};

// Export global
if (typeof window !== 'undefined') {
  window.Knowledge = Knowledge;
}
