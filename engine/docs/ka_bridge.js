/**
 * KA Bridge — Transfert bilatéral Médecin ↔ Patient
 * ===================================================
 * Format standardisé d'échange de données médicales.
 * Utilisé par KA Care (médecin) et KA Patient.
 * 
 * Transfert : QR code, copier-coller JSON, ou code court.
 * Aucun cloud — tout passe en local.
 */

const KA_BRIDGE = {
  VERSION: '1.0',
  
  /**
   * Crée un paquet de transfert Médecin → Patient.
   * Le médecin envoie : diagnostic, prescriptions, conseils.
   */
  doctorToPatient(diagnosisResult, patientInfo) {
    return {
      version: this.VERSION,
      type: 'doctor_to_patient',
      timestamp: new Date().toISOString(),
      doctor: patientInfo?.doctor || 'KA Care',
      patient: {
        name: patientInfo?.name || '',
        id: patientInfo?.id || ''
      },
      diagnosis: {
        primary: diagnosisResult?.diagnostic_principal?.maladie || '',
        score: diagnosisResult?.diagnostic_principal?.score || 0,
        differentials: (diagnosisResult?.diagnostics_différentiels || []).slice(0, 3).map(d => ({
          name: d.maladie, score: d.score
        })),
        symptoms: diagnosisResult?.diagnostic_principal?.symptomes_attendus || [],
        advice: diagnosisResult?.diagnostic_principal?.conduite || '',
        urgency: diagnosisResult?.diagnostic_principal?.urgence || false,
        delay: diagnosisResult?.diagnostic_principal?.delai || ''
      },
      prescriptions: [],
      notes: ''
    };
  },

  /**
   * Crée un paquet de transfert Patient → Médecin.
   * Le patient envoie : profil, constantes, médicaments, allergies.
   */
  patientToDoctor(patientData) {
    return {
      version: this.VERSION,
      type: 'patient_to_doctor',
      timestamp: new Date().toISOString(),
      profile: patientData.profile || {},
      vitals: (patientData.vitals || []).slice(-10),
      medications: patientData.medications || [],
      allergies: patientData.allergies || [],
      vaccines: patientData.vaccines || [],
      appointments: patientData.appointments || []
    };
  },

  /**
   * Encode un paquet en chaîne compacte (pour QR code).
   */
  encode(data) {
    return btoa(unescape(encodeURIComponent(JSON.stringify(data))));
  },

  /**
   * Décode une chaîne compacte en paquet.
   */
  decode(encoded) {
    try {
      return JSON.parse(decodeURIComponent(escape(atob(encoded))));
    } catch(e) {
      return null;
    }
  },

  /**
   * Importe les données patient dans KA Care (côté médecin).
   */
  importToKACare(patientPackage) {
    if (!patientPackage || patientPackage.type !== 'patient_to_doctor') return false;
    
    // Stocker dans le localStorage de KA Care
    const existing = JSON.parse(localStorage.getItem('ka_care_patients') || '{}');
    const id = patientPackage.profile?.id || ('p' + Date.now());
    
    existing[id] = {
      name: patientPackage.profile?.name || 'Patient importé',
      age: patientPackage.profile?.age || '',
      gender: patientPackage.profile?.gender || '',
      blood: patientPackage.profile?.blood || '',
      weight: patientPackage.profile?.weight || '',
      allergies: patientPackage.allergies || [],
      vaccines: patientPackage.vaccines || [],
      history: [patientPackage.profile?.history || ''],
      vitals: patientPackage.vitals || [],
      medications: patientPackage.medications || [],
      appointments: patientPackage.appointments || [],
      importedAt: new Date().toISOString()
    };
    
    localStorage.setItem('ka_care_patients', JSON.stringify(existing));
    return id;
  },

  /**
   * Importe les données médecin dans KA Patient (côté patient).
   */
  importToKAPatient(doctorPackage) {
    if (!doctorPackage || doctorPackage.type !== 'doctor_to_patient') return false;
    
    // Ajouter aux rendez-vous du patient
    const pdata = JSON.parse(localStorage.getItem('ka_patient_data') || '{}');
    if (!pdata.appointments) pdata.appointments = [];
    
    // Ajouter le diagnostic comme un rendez-vous de suivi
    pdata.appointments.push({
      title: 'Suivi — ' + (doctorPackage.diagnosis?.primary || 'Consultation'),
      date: new Date().toISOString().split('T')[0],
      time: '',
      loc: 'KA Care — ' + (doctorPackage.doctor || 'Médecin'),
      diagnosis: doctorPackage.diagnosis,
      notes: doctorPackage.notes || ''
    });
    
    // Ajouter les prescriptions
    if (!pdata.medications) pdata.medications = [];
    (doctorPackage.prescriptions || []).forEach(p => {
      pdata.medications.push({
        name: p.name, dose: p.dose, freq: p.freq, time: p.time || '08:00',
        meal: p.meal || '', added: new Date().toISOString()
      });
    });
    
    localStorage.setItem('ka_patient_data', JSON.stringify(pdata));
    return true;
  },

  /**
   * Génère un QR code pour le transfert de données.
   * Utilise l'API QR Code (si disponible) ou affiche le code en texte.
   */
  generateQRCode(data, elementId) {
    const encoded = this.encode(data);
    const el = document.getElementById(elementId);
    if (!el) return;
    
    // Afficher comme texte compact (QR code visuel si bibliothèque dispo)
    // Utiliser le QR code visuel de KA_SECURE si disponible
if (typeof KA_SECURE !== 'undefined' && KA_SECURE.generateQR) {
KA_SECURE.generateQR(elementId, data);
} else {
el.innerHTML = '<div style="background:#fff;color:#000;padding:20px;border-radius:12px;text-align:center;font-size:11px;word-break:break-all;max-height:200px;overflow-y:auto">' + 
      encoded.substring(0, 500) + 
      '</div>' +
      '<button onclick="navigator.clipboard.writeText(\'' + encoded + '\')" style="margin-top:8px;background:#1a1a1a;color:#d4a853;border:1px solid #2a2a2a;padding:8px 16px;border-radius:8px;cursor:pointer;font-family:inherit">📋 Copier le code</button>' +
      '}<p style="font-size:10px;color:#8b7355;margin-top:6px">Code de transfert KA Bridge — valable 24h</p>';
    
    return encoded;
  },

  /**
   * Lit un code de transfert (depuis le presse-papier ou saisie manuelle).
   */
  readTransferCode(callback) {
    const code = prompt('Collez le code de transfert :');
    if (!code) return;
    const data = this.decode(code);
    if (!data) {
      alert('Code invalide ou corrompu.');
      return;
    }
    callback(data);
  }
};

/**
 * KA AI — Pont vers l'API hologrammes HWAT
 * =========================================
 * Interroge le serveur d'inférence local (hologrammes médicaux).
 * Fallback silencieux : si l'API est absente, l'app continue
 * en mode 100% local (diagnostic cosinus sur DB).
 */
const KA_AI = {
  API_URL: 'http://localhost:8010/hologram/query',
  TIMEOUT_MS: 3000,

  /**
   * Interroge les hologrammes médicaux.
   * @returns {Promise<Array>} faits pertinents (ou [] si API absente)
   */
  async query(text, topK = 4) {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), this.TIMEOUT_MS);
      const resp = await fetch(this.API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain: 'auto', query: text, top_k: topK }),
        signal: controller.signal
      });
      clearTimeout(timer);
      if (!resp.ok) return [];
      const data = await resp.json();
      return (data.results || []).filter(r => r.score > 0.15);
    } catch (e) {
      return []; // API non joignable → mode local
    }
  },

  /**
   * HTML des faits holographiques (affiché sous le diagnostic local).
   */
  renderFacts(facts) {
    if (!facts.length) return '';
    const rows = facts.slice(0, 4).map(f =>
      '<div style="padding:8px 12px;border-left:3px solid #4caf50;background:rgba(76,175,80,.06);border-radius:6px;margin:6px 0;font-size:13px">' +
      '<span style="color:#4caf50;font-size:11px;text-transform:uppercase;letter-spacing:1px">Hologramme ' + f.secteur + ' · ' + (f.score * 100).toFixed(0) + '%</span><br>' +
      escapeHtml(f.content) +
      '</div>'
    ).join('');
    return '<div class="card"><h3 style="margin-top:0">🌿 Base de connaissances (hologrammes)</h3>' + rows + '</div>';
  }
};

/** Échappe le HTML pour les contenus externes. */
function escapeHtml(s) {
  return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
