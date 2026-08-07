/**
 * Vital Ka Hologram — Encodeur de Santé Harmonique
 * =================================================
 * Encode l'état complet d'un patient en hologramme C^512.
 * ~200 dimensions réelles mappées en vecteur complexe
 * via FNV-1a hashing + phi-spacing.
 * 
 * Niveaux :
 *   1. Actuel (45-86 features) : encodeSympt() dans ka_core.js
 *   2. Enrichi (~200 features) : encodeHologram() ici
 *   3. Complet (512 complexe) : holoFull()
 * 
 * Usage :
 *   const holo = Hologram.encode(symptoms, vitals, patientData);
 *   const similar = Hologram.cosineSim(holo1, holo2);
 *   Hologram.explain(holo); // visualisation
 */

const Hologram = {
  PHI: 1.618033988749895,
  DIM: 512,
  
  /**
   * FNV-1a 64-bit (simplifié pour JS)
   * Retourne un hash entre 0 et 1
   */
  _hash(str) {
    let h = 0xcbf29ce484222325n;
    for (let i = 0; i < str.length; i++) {
      h ^= BigInt(str.charCodeAt(i));
      h *= 0x100000001b3n;
    }
    return Number(h & 0xFFFFFFFFFFFFn) / 0xFFFFFFFFFFFF;
  },
  
  /**
   * Encode un mot en angle phi-space dans C^512
   * angle = (hash * phi * 2pi) % 2pi
   */
  _wordToAngle(word) {
    const h = this._hash(word.toLowerCase());
    return (h * this.PHI * 2 * Math.PI) % (2 * Math.PI);
  },
  
  /**
   * Projette un angle + amplitude sur le cercle unitaire complexe
   * Retourne {real, imag} normalise
   */
  _project(angle, amplitude = 1.0) {
    return {
      real: Math.cos(angle) * amplitude,
      imag: Math.sin(angle) * amplitude
    };
  },
  
  /**
   * Encode un hologramme complet du patient
   * @param {Object} data - Donnees patient completes
   * @param {string} data.symptoms - Texte des symptomes
   * @param {Object} data.vitals - Constantes vitales {hr, bp, spo2, temp, weight, height}
   * @param {Array} data.history - Historique medical ['maladie1', 'maladie2']
   * @param {Object} data.demographics - {age, gender, blood}
   * @param {Array} data.medications - Medicaments [{name, dose, freq}]
   * @param {Object} data.context - {season, region, travel, exposure}
   * @param {Array} data.allergies - ['pollen', 'penicilline', ...]
   * @param {Array} data.riskFactors - ['smoking', 'diabetes', ...]
   * @param {Object} data.temporal - {onset, duration, pattern, progression}
   * @returns {{ vector: Float64Array, dims: number, features: string[] }}
   */
  encode(data = {}) {
    const features = [];
    const vector = new Float64Array(this.DIM * 2); // real + imag interleaved
    
    const add = (name, weight = 1.0) => {
      const angle = this._wordToAngle(name);
      const proj = this._project(angle, weight);
      const idx = Math.floor(this._hash(name) * this.DIM);
      vector[idx * 2] += proj.real;
      vector[idx * 2 + 1] += proj.imag;
      features.push(name + ':' + weight.toFixed(1));
    };
    
    // 1. SYMPTOMES (depuis ka_core.js encodeSympt)
    if (data.symptoms) {
      const words = data.symptoms.toLowerCase().replace(/[,;.!?]/g, ' ').split(/\s+/).filter(w => w.length > 1);
      words.forEach(w => add('sym_' + w, 2.0));
    }
    
    // 2. VITAUX
    const v = data.vitals || {};
    if (v.hr) {
      if (v.hr > 100) add('tachycardia', 3.0);
      else if (v.hr < 60) add('bradycardia', 3.0);
      else add('hr_normal', 1.0);
    }
    if (v.spo2) {
      if (v.spo2 < 90) add('hypoxia_severe', 4.0);
      else if (v.spo2 < 95) add('hypoxia_mild', 2.0);
      else add('spo2_normal', 0.5);
    }
    if (v.temp) {
      if (v.temp > 39) add('fever_high', 3.0);
      else if (v.temp > 38) add('fever_moderate', 2.0);
      else if (v.temp > 37.2) add('fever_mild', 1.0);
      else if (v.temp < 35.5) add('hypothermia', 3.0);
      else add('temp_normal', 0.5);
    }
    if (v.bp) {
      const [sys, dia] = String(v.bp).split('/').map(Number);
      if (sys > 140) add('hypertension', 2.0);
      else if (sys < 90) add('hypotension', 3.0);
      if (dia > 90) add('diastolic_high', 1.5);
    }
    if (v.weight) add('weight_' + Math.round(v.weight), 0.5);
    if (v.height) add('height_' + Math.round(v.height), 0.3);
    
    // 3. DEMOGRAPHICS
    const d = data.demographics || {};
    if (d.age) {
      const age = parseInt(d.age) || 0;
      if (age <= 5) add('age_infant', 2.0);
      else if (age <= 12) add('age_child', 1.5);
      else if (age <= 17) add('age_adolescent', 1.0);
      else if (age <= 40) add('age_young_adult', 1.0);
      else if (age <= 65) add('age_adult', 1.5);
      else add('age_elderly', 2.5);
      if (age > 50) add('risk_age', 2.0);
    }
    if (d.gender) add('gender_' + d.gender, 1.0);
    if (d.blood) add('blood_' + d.blood.replace(/[+-]/g, ''), 0.5);
    
    // 4. HISTORIQUE MEDICAL
    (data.history || []).forEach(h => add('hx_' + h, 2.0));
    
    // 5. MEDICAMENTS
    (data.medications || []).forEach(m => {
      add('med_' + m.name, 1.5);
      if (m.dose) add('dose_' + m.dose, 0.5);
    });
    
    // 6. CONTEXTE
    const c = data.context || {};
    if (c.season) add('season_' + c.season, 1.5);
    if (c.region) add('region_' + c.region, 2.0);
    if (c.travel) add('travel_' + c.travel, 2.5);
    if (c.exposure) add('exposure_' + c.exposure, 2.0);
    if (c.outbreak) add('outbreak_' + c.outbreak, 3.0);
    
    // 7. ALLERGIES
    (data.allergies || []).forEach(a => add('allergy_' + a, 1.5));
    
    // 8. FACTEURS DE RISQUE
    (data.riskFactors || []).forEach(r => add('risk_' + r, 2.5));
    
    // 9. PATTERNS TEMPORELS
    const t = data.temporal || {};
    if (t.onset) add('onset_' + t.onset, 2.0);
    if (t.duration) add('duration_' + t.duration, 2.0);
    if (t.pattern) add('pattern_' + t.pattern, 2.5);
    if (t.progression) add('progression_' + t.progression, 2.0);
    
    // 10. LIFESTYLE
    const l = data.lifestyle || {};
    if (l.diet) add('diet_' + l.diet, 1.0);
    if (l.activity) add('activity_' + l.activity, 1.0);
    if (l.sleep) add('sleep_' + l.sleep, 1.5);
    if (l.stress) add('stress_' + l.stress, 1.5);
    
    // Normaliser le vecteur (projection sur sphere unite)
    let norm = 0;
    for (let i = 0; i < vector.length; i++) norm += vector[i] * vector[i];
    if (norm > 0) {
      norm = Math.sqrt(norm);
      for (let i = 0; i < vector.length; i++) vector[i] /= norm;
    }
    
    return { vector, dims: features.length, features };
  },
  
  /**
   * Cosine similarity entre deux hologrammes
   */
  cosineSim(a, b) {
    let dot = 0, na = 0, nb = 0;
    const len = Math.min(a.vector.length, b.vector.length);
    for (let i = 0; i < len; i++) {
      dot += a.vector[i] * b.vector[i];
      na += a.vector[i] * a.vector[i];
      nb += b.vector[i] * b.vector[i];
    }
    return dot / (Math.sqrt(na) * Math.sqrt(nb) + 1e-10);
  },
  
  /**
   * Distance harmonique (1 - cosine)
   */
  distance(a, b) {
    return 1 - this.cosineSim(a, b);
  },
  
  /**
   * Explique l'hologramme en texte lisible
   */
  explain(holo) {
    if (!holo || !holo.features) return 'Hologramme vide';
    
    const groups = {};
    holo.features.forEach(f => {
      const [group] = f.split('_');
      if (!groups[group]) groups[group] = [];
      groups[group].push(f);
    });
    
    let text = '';
    const labels = {
      sym: 'Symptomes', hx: 'Historique', med: 'Medicaments',
      age: 'Age', gender: 'Genre', blood: 'Sang',
      risk: 'Risques', allergy: 'Allergies',
      season: 'Saison', region: 'Region', travel: 'Voyage',
      exposure: 'Exposition', outbreak: 'Epidemie',
      onset: 'Debut', duration: 'Duree', pattern: 'Pattern',
      progression: 'Progression',
      tachycardia: 'Cardiaque', bradycardia: 'Cardiaque',
      fever: 'Temperature', hypoxia: 'Oxygenation',
      hypertension: 'Tension', hypotension: 'Tension',
      hr_normal: 'Cardiaque', spo2_normal: 'Oxygenation', temp_normal: 'Temperature'
    };
    
    for (const [group, feats] of Object.entries(groups)) {
      const label = labels[group] || group;
      text += '\n' + label + ' (' + feats.length + '): ';
      text += feats.map(f => f.split(':')[0].replace(group + '_', '')).slice(0, 5).join(', ');
      if (feats.length > 5) text += '...';
    }
    
    return text.trim();
  },
  
  /**
   * Compare deux hologrammes et retourne les differences
   */
  diff(a, b) {
    const sim = this.cosineSim(a, b);
    const featA = new Set(a.features.map(f => f.split(':')[0]));
    const featB = new Set(b.features.map(f => f.split(':')[0]));
    const common = [...featA].filter(f => featB.has(f));
    const onlyA = [...featA].filter(f => !featB.has(f));
    const onlyB = [...featB].filter(f => !featA.has(f));
    
    return {
      similarity: sim,
      commonFeatures: common.length,
      onlyInFirst: onlyA.length,
      onlyInSecond: onlyB.length,
      common,
      onlyA,
      onlyB
    };
  }
};

// Export global
if (typeof window !== 'undefined') {
  window.Hologram = Hologram;
}
