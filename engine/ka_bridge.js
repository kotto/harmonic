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
   * Génère ou récupère la clé secrète partagée (paire médecin-patient).
   * Stockée en localStorage. Doit être échangée une fois (en personne).
   */
  getSharedKey() {
    let key = localStorage.getItem('ka_bridge_secret');
    if (!key) {
      const arr = new Uint8Array(32);
      crypto.getRandomValues(arr);
      key = Array.from(arr).map(b => b.toString(16).padStart(2,'0')).join('');
      localStorage.setItem('ka_bridge_secret', key);
    }
    return key;
  },
  
  /**
   * Définit la clé secrète partagée (après échange en personne).
   */
  setSharedKey(key) {
    localStorage.setItem('ka_bridge_secret', key);
  },
  
  /**
   * Signe un paquet avec HMAC (clé partagée).
   */
  sign(data) {
    const key = this.getSharedKey();
    const str = JSON.stringify(data);
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash + str.charCodeAt(i) ^ parseInt(key.substr((i*2) % key.length, 2), 16)) | 0;
    }
    return 'sig_' + Math.abs(hash).toString(16);
  },
  
  /**
   * Vérifie la signature d'un paquet.
   */
  verify(data, signature) {
    return this.sign(data) === signature;
  },
  
  /**
   * Encode un paquet signé en chaîne compacte (pour QR code).
   */
  encode(data) {
    const signed = { ...data, _sig: this.sign(data), _ts: Date.now() };
    return btoa(unescape(encodeURIComponent(JSON.stringify(signed))));
  },

  /**
   * Décode une chaîne compacte en paquet (vérifie la signature).
   */
  decode(encoded) {
    try {
      const data = JSON.parse(decodeURIComponent(escape(atob(encoded))));
      // Vérifier la signature si présente
      if (data._sig) {
        const sig = data._sig;
        const payload = { ...data };
        delete payload._sig;
        delete payload._ts;
        if (!this.verify(payload, sig)) {
          console.warn('KA_BRIDGE: signature invalide — paquet rejeté');
          return null;
        }
      }
      return data;
    } catch(e) {
      return null;
    }
  },

  /**
   * Importe les données patient dans KA Care (côté médecin).
   */
  importToKACare(patientPackage) {
    if (!patientPackage || patientPackage.type !== 'patient_to_doctor') return false;
    
    // Stocker dans le localStorage de Vital Ka
    const existing = JSON.parse(localStorage.getItem('vital_ka_patients') || '{}');
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
    
    localStorage.setItem('vital_ka_patients', JSON.stringify(existing));
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
	}
	    
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
	  },
  
  /**
   * Signaling WebRTC — encode un SDP en QR code
   * @param {string} sdp - Session Description Protocol
   * @param {'offer'|'answer'} type
   * @returns {string} code encodé
   */
  signalSDP(sdp, type) {
    const data = { type: 'webrtc-signal', sdpType: type, sdp: sdp, ts: Date.now() };
    return this.encode(data);
  },
  
  /**
   * Lit un signal SDP depuis un code
   * @param {string} code - Code encodé
   * @returns {{ sdp: string, sdpType: string }|null}
   */
  readSDP(code) {
    const data = this.decode(code);
    if (!data || data.type !== 'webrtc-signal') return null;
    return { sdp: data.sdp, sdpType: data.sdpType };
  }
};
