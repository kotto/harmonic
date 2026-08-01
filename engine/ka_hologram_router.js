/**
 * KA Hologram Router — Routeur spectral médical OFFLINE
 * ======================================================
 * Portage JS du routeur Python (hologram_router.py) pour l'APK
 * Capacitor. Charge le bundle embarqué (data/hologram_bundle.json)
 * et répond 100% hors-ligne — aucune API nécessaire.
 *
 * Fonctionnalités :
 *   - Routage : question → top domaines (index lexical pré-calculé)
 *   - Retrieval : faits pertinents par chevauchement pondéré
 *   - Phrasé naturel : templates par relation médicale
 *   - Seuil de confiance : "je ne sais pas" au lieu d'inventer
 *
 * Usage :
 *   await KA_HOLOGRAM.load();                    // charge le bundle
 *   const r = KA_HOLOGRAM.query('fièvre toux');  // réponse structurée
 */

const KA_HOLOGRAM = {
  bundle: null,
  loaded: false,
  MIN_SCORE: 0.15,
  STOP: new Set(['le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou',
    'au', 'aux', 'en', 'pour', 'avec', 'sur', 'est', 'sont', 'ce',
    'cette', 'dans', 'à', 'a', 'mon', 'ma', 'mes', 'son', 'sa',
    'ses', 'qui', 'que', 'si', 'par', 'pas', 'plus', 'parmi',
    'chez', 'sans', 'sous', 'vers', 'depuis', 'pendant', 'entre']),

  /** Charge le bundle embarqué (lazy, une seule fois). */
  async load() {
    if (this.loaded) return true;
    try {
      const resp = await fetch('data/hologram_bundle.json');
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      this.bundle = await resp.json();
      this.loaded = true;
      console.log('🌿 KA Hologram : ' + Object.keys(this.bundle.domains).length +
                  ' domaines, ' + this._totalFacts() + ' faits chargés');
      return true;
    } catch (e) {
      console.warn('KA Hologram bundle indisponible :', e.message);
      return false;
    }
  },

  _totalFacts() {
    let n = 0;
    for (const d of Object.values(this.bundle.domains)) n += d.facts.length;
    return n;
  },

  /** Tokenise une phrase (mots significatifs). */
  _tokenize(text) {
    const words = String(text || '').toLowerCase()
      .match(/[a-zà-ÿ0-9]+/g) || [];
    return words.filter(w => w.length > 2 && !this.STOP.has(w));
  },

  /**
   * Routage : question → [domaine, confidence] triés.
   * Score = mots-clés du vocabulaire du domaine présents dans la question.
   */
  route(question, topK = 3) {
    if (!this.loaded) return [];
    const qWords = this._tokenize(question);
    if (!qWords.length) return [];

    const scores = {};
    for (const [domain, d] of Object.entries(this.bundle.domains)) {
      const vocabSet = new Set(d.vocab);
      let hit = 0;
      for (const w of qWords) if (vocabSet.has(w)) hit++;
      if (hit > 0) scores[domain] = hit;
    }

    const entries = Object.entries(scores).sort((a, b) => b[1] - a[1]).slice(0, topK);
    const total = entries.reduce((s, e) => s + e[1], 0) || 1;
    return entries.map(([d, s]) => [d, s / total]);
  },

  /**
   * Retrieval : faits pertinents du domaine, score normalisé [0,1].
   * Poids : sujet 3× > objet 2× > relation 1×.
   */
  retrieveFacts(domain, question, topK = 5) {
    if (!this.loaded || !this.bundle.domains[domain]) return [];
    const qWords = this._tokenize(question);
    if (!qWords.length) return [];

    const scored = [];
    const qSet = new Set(qWords);
    for (const [s, r, o] of this.bundle.domains[domain].facts) {
      const sWords = new Set(this._tokenize(s));
      const oWords = new Set(this._tokenize(o));
      const rWords = new Set(this._tokenize(r));
      let interS = 0, interO = 0, interR = 0;
      for (const w of qSet) {
        if (sWords.has(w)) interS++;
        if (oWords.has(w)) interO++;
        if (rWords.has(w)) interR++;
      }
      let score = (interS * 3 + interO * 2 + interR * 1) / Math.max(qWords.length * 3, 1);
      // Bonus sous-chaîne (dérivés : fièvre/élevée)
      const sl = s.toLowerCase(), ol = o.toLowerCase();
      for (const w of qWords) {
        if (w.length > 3 && (sl.includes(w) || ol.includes(w))) score += 0.25;
      }
      if (score > 0) scored.push({ score, s, r, o });
    }

    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, topK).map(f => ({
      ...f,
      score: Math.min(1.0, Math.round(f.score * 1000) / 1000),
      phrase: this._formatPhrase(f.s, f.r, f.o),
    }));
  },

  /** Phrasé naturel : template par relation. */
  _formatPhrase(s, r, o) {
    const templates = this.bundle.templates || {};
    const DEFAULT = this.bundle.default_template || 'Information sur {s} : {o}.';
    const rClean = String(r || '').trim().toLowerCase().replace(/ /g, '_');
    const baseR = rClean.includes('_') ? rClean.split('_')[0] : rClean;
    const tpl = templates[rClean] || templates[baseR] || DEFAULT;
    try {
      return tpl.replace('{s}', s).replace('{o}', o);
    } catch (e) {
      return DEFAULT.replace('{s}', s).replace('{o}', o);
    }
  },

  /**
   * Requête complète : route → retrieve → réponse structurée.
   * Retourne { domain, results: [{sujet, relation, objet, score, phrase}], bestScore }
   */
  query(question, topK = 4) {
    // ── Règle de couverture lexicale : si moins de 50% des mots de la
    //    question existent dans le vocabulaire médical embarqué, c'est
    //    très probablement un hors-sujet (football, cuisine...) qui
    //    matcherait par coïncidence des faits ("transfert hospitalier").
    const qWords = this._tokenize(question);
    if (qWords.length) {
      const globalVocab = new Set();
      for (const d of Object.values(this.bundle.domains)) {
        for (const w of d.vocab) globalVocab.add(w);
      }
      let known = 0;
      for (const w of qWords) if (globalVocab.has(w)) known++;
      const coverage = known / qWords.length;
      if (coverage < 0.5) {
        return {
          domain: 'INCONNU',
          results: [{
            sujet: '', relation: '', objet: 'hors domaine',
            score: 0, secteur: 'INCONNU',
            phrase: 'Aucune correspondance fiable. Cette question ne relève pas des connaissances médicales Vital Ka. Consultez un professionnel de santé.',
          }],
          bestScore: 0,
        };
      }
    }

    const routes = this.route(question, 3);
    if (!routes.length) return { domain: 'INCONNU', results: [], bestScore: 0 };

    const seen = new Set();
    const results = [];
    let bestScore = 0;

    for (const [domain] of routes) {
      for (const f of this.retrieveFacts(domain, question, topK)) {
        const key = f.s + '|' + f.r + '|' + f.o;
        if (seen.has(key)) continue;
        seen.add(key);
        bestScore = Math.max(bestScore, f.score);
        results.push({
          sujet: f.s, relation: f.r, objet: f.o,
          score: f.score, phrase: f.phrase, secteur: domain,
        });
      }
    }

    results.sort((a, b) => b.score - a.score);

    // Seuil de confiance : mieux vaut "je ne sais pas"
    if (bestScore < this.MIN_SCORE) {
      return {
        domain: routes[0][0],
        results: [{
          sujet: '', relation: '', objet: 'hors domaine',
          score: 0, secteur: routes[0][0],
          phrase: 'Aucune correspondance fiable. Cette question ne relève pas des connaissances médicales Vital Ka ou manque de précision. Consultez un professionnel de santé.',
        }],
        bestScore: 0,
      };
    }

    return { domain: routes[0][0], results: results.slice(0, topK * 2), bestScore };
  },

  /** HTML prêt à afficher sous le diagnostic local. */
  renderHTML(results) {
    if (!results || !results.length) return '';
    const rows = results.filter(r => r.score > 0.15).slice(0, 4).map(r =>
      '<div style="padding:8px 12px;border-left:3px solid #4caf50;background:rgba(76,175,80,.06);border-radius:6px;margin:6px 0;font-size:13px">' +
      '<span style="color:#4caf50;font-size:11px;text-transform:uppercase;letter-spacing:1px">Hologramme ' +
      (r.secteur || '') + ' · ' + Math.round((r.score || 0) * 100) + '%</span><br>' +
      this._escapeHtml(r.phrase) +
      '</div>'
    ).join('');
    return '<div class="card"><h3 style="margin-top:0">🌿 Base de connaissances (hologrammes)</h3>' + rows + '</div>';
  },

  _escapeHtml(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  },

  /**
   * Vérifie les interactions entre médicaments (100% offline).
   * Parité avec l'endpoint /interactions de l'API Python :
   * pour chaque médicament, on cherche les faits d'interaction du domaine
   * PHARMACIE dont le sujet (ex: "diazepam + alcool + opiacés") contient
   * ce médicament — matching par sous-chaîne, robuste aux accents.
   * @returns {Array} [{s, r, o, phrase, severity}]
   */
  checkInteractions(medications, topK = 8) {
    if (!this.loaded || !this.bundle.domains['PHARMACIE']) return [];
    const normalize = (t) => String(t || '').toLowerCase()
      .replace(/é/g, 'e').replace(/è/g, 'e').replace(/ê/g, 'e')
      .replace(/à/g, 'a').replace(/â/g, 'a').replace(/ô/g, 'o')
      .replace(/î/g, 'i').replace(/û/g, 'u').replace(/ç/g, 'c');
    const meds = medications.map(m => normalize(m)).filter(m => m.trim());

    const results = [];
    const seen = new Set();
    for (const [s, r, o] of this.bundle.domains['PHARMACIE'].facts) {
      if (!String(r).includes('interaction')) continue;
      const sNorm = normalize(s);
      if (!meds.some(m => sNorm.includes(m))) continue;
      const key = s + '|' + o;
      if (seen.has(key)) continue;
      seen.add(key);
      const txt = (s + ' ' + o).toLowerCase();
      let severity = 'minor';
      if (/contre-indiqu|risque mortel|jamais/.test(txt)) severity = 'contraindicated';
      else if (/majeur|grave|danger|hémorrag/.test(txt)) severity = 'major';
      else if (/modéré|surveiller/.test(txt)) severity = 'moderate';
      results.push({
        s, r, o,
        phrase: this._formatPhrase(s, r, o),
        severity,
        score: 0.9,
      });
    }
    const order = { contraindicated: 5, major: 4, moderate: 3, minor: 2 };
    results.sort((a, b) => (order[b.severity] || 1) - (order[a.severity] || 1));
    return results.slice(0, topK);
  }
};

if (typeof window !== 'undefined') window.KA_HOLOGRAM = KA_HOLOGRAM;
