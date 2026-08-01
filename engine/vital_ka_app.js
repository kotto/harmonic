/**
 * Vital Ka App — Logique métier (extracted from vital_ka.html)
 * =============================================================
 * Gère : patients, diagnostic, historique, vitals, navigation
 * Dépendances : ka_core.js (DB, encodeSympt, cosineSim, F)
 *               ka_secure.js, ka_bridge.js, vital_ka_ble.js
 */

// ── Migration des anciennes clés localStorage 'ka_care_*' → 'vital_ka_*' ──
// Idempotent : copie ancienne→nouvelle puis supprime l'ancienne. Préserve
// l'historique et les patients des utilisateurs existants (rebrand KA Care→Vital Ka).
(function _migrateKeys() {
  if (typeof localStorage === 'undefined') return;
  const MAP = {
    'ka_care_patients': 'vital_ka_patients',
    'ka_care_history': 'vital_ka_history',
    'ka_care_phyto_off': 'vital_ka_phyto_off',
    'ka_care_specialty': 'vital_ka_specialty',
  };
  for (const [oldK, newK] of Object.entries(MAP)) {
    if (localStorage.getItem(oldK) !== null && localStorage.getItem(newK) === null) {
      localStorage.setItem(newK, localStorage.getItem(oldK));
      localStorage.removeItem(oldK);
    }
  }
})();

const PK = 'vital_ka_patients';
let currentPatient = null;
let diagnosticHistory = JSON.parse(localStorage.getItem('vital_ka_history') || '[]');
let currentScreen = 'splash';

// ── Pile de navigation (bouton retour / flèche ←) ──
// On pousse l'écran quitté ; goBack() dépile. 'splash' n'est jamais poussé
// (point de sortie de l'app — bouton retour sur splash = quitter).
let navigationStack = [];

// ═══ PATIENTS ═══
function loadPatients() { try { return JSON.parse(localStorage.getItem(PK) || '{}'); } catch (e) { return {}; } }
function savePatients(pts) { localStorage.setItem(PK, JSON.stringify(pts)); }

// ── Code court d'identification patient (6 caractères base32) ──
// Dérivé déterministe de l'ID — stable, lisible, sans ambiguïtés (0/O/1/I exclus).
// Format : "K7M2-XQ". Permet d'identifier un patient sans réseau ni QR.
const SHORT_CODE_ALPHABET = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ';
function generateShortCode(seed) {
  // Hash simple et déterministe depuis la chaîne seed (l'ID patient)
  let h = 0;
  for (let i = 0; i < seed.length; i++) { h = ((h << 5) - h + seed.charCodeAt(i)) | 0; }
  h = Math.abs(h) || 1;
  let code = '';
  for (let i = 0; i < 6; i++) {
    code += SHORT_CODE_ALPHABET[h % SHORT_CODE_ALPHABET.length];
    h = Math.floor(h / SHORT_CODE_ALPHABET.length) + (i + 1) * 7;
  }
  return code.slice(0, 3) + '-' + code.slice(3);
}

function refreshPatientSelect() {
  const pts = loadPatients();
  const sel = document.getElementById('patientSelect');
  if (!sel) return;
  sel.innerHTML = '<option value="">👤 Patient anonyme</option>';
  for (const [id, p] of Object.entries(pts)) {
    sel.innerHTML += '<option value="' + id + '">' + KA_SECURE.escapeHtml(p.name) + ' (' + (p.history ? p.history.length : 0) + ' diags)</option>';
  }
}
function onPatientSelect(id) {
  const pts = loadPatients();
  currentPatient = id && pts[id] ? { id, ...pts[id] } : null;
  updateDossier();
}

// ═══ DOSSIER ═══
function updateDossier() {
  const av = document.getElementById('dossierAvatar');
  const nm = document.getElementById('dossierName');
  const idEl = document.getElementById('dossierId');
  if (!av || !nm || !idEl) return;
  if (!currentPatient) {
    av.textContent = '?'; nm.textContent = 'Patient anonyme'; idEl.textContent = '';
  } else {
    av.textContent = (currentPatient.name || '?')[0].toUpperCase();
    nm.textContent = currentPatient.name;
    // Identité complète : âge, sexe, groupe sanguin, code court
    const parts = [];
    if (currentPatient.age) parts.push(currentPatient.age + ' ans');
    if (currentPatient.gender === 'homme') parts.push('Homme');
    else if (currentPatient.gender === 'femme') parts.push('Femme');
    if (currentPatient.blood) parts.push('⚖ ' + currentPatient.blood);
    if (currentPatient.weight) parts.push(currentPatient.weight + ' kg');
    let idLine = parts.join(' · ');
    if (currentPatient.shortCode) idLine += '  ·  🔑 code ' + currentPatient.shortCode;
    idEl.textContent = idLine;
  }
  // ── Branchement des constantes vitales (vrai data si dispo) ──
  const setStat = (id, val, suffix) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = (val !== undefined && val !== null && val !== '') ? val + (suffix || '') : '--';
  };
  // Recherche des dernières constantes : historique patient > barre de diag > '--'
  const v = _latestVitalsFor(currentPatient);
  setStat('dosBPM', v.bpm);
  setStat('dosBP', v.bp);
  setStat('dosSpO2', v.spo2);
  setStat('dosTemp', v.temp, v.temp ? '°' : '');
}

// Extrait les dernières constantes vitales connues pour un patient.
// Source prioritaire : champs vitals[] importés ; sinon signes vitaux de la
// barre de diagnostic courante (vitalTASyst, vitalFR, vitalTemp...).
function _latestVitalsFor(p) {
  const out = { bpm: null, bp: null, spo2: null, temp: null };
  if (p && Array.isArray(p.vitals) && p.vitals.length) {
    const last = p.vitals[p.vitals.length - 1];
    out.bpm = last.bpm || last.fc || null;
    out.bp = last.bp || (last.taSyst ? last.taSyst + '/' + (last.taDiast || '') : null);
    out.spo2 = last.spo2 || null;
    out.temp = last.temp || null;
  }
  // Complète avec la barre de diagnostic courante (saisie en cours)
  const fld = (id) => { const e = document.getElementById(id); return e && e.value ? e.value : null; };
  if (!out.temp) out.temp = fld('vitalTemp');
  if (!out.bp) {
    const s = fld('vitalTASyst'), d = fld('vitalTADiast');
    if (s) out.bp = s + (d ? '/' + d : '');
  }
  if (!out.bpm) out.bpm = fld('vitalFR'); // FR comme approximation affichée si pas de FC
  return out;
}

// ═══ SCREENS ═══
// Badge santé du serveur vocal Piper (écran IA) — non bloquant, 2.5s max
async function updateVoiceServerBadge() {
  const el = document.getElementById('voiceServerBadge');
  if (!el) return;

  // Mode natif Android : pas de serveur Piper → voix système du téléphone
  if (typeof VITAL_KA_CONFIG !== 'undefined' &&
      VITAL_KA_CONFIG.platform && VITAL_KA_CONFIG.platform.isNative) {
    el.className = 'voice-server-badge online';
    el.textContent = '🎙️ Voix native';
    el.title = 'Voix système Android (TTS) — pas de serveur Piper en mode natif';
    return;
  }

  const base = (typeof VITAL_KA_CONFIG !== 'undefined')
    ? VITAL_KA_CONFIG.voiceServerUrl : 'http://localhost:8420';
  const timeout = (typeof VITAL_KA_CONFIG !== 'undefined' && VITAL_KA_CONFIG.voice)
    ? VITAL_KA_CONFIG.voice.healthTimeoutMs : 2500;
  el.className = 'voice-server-badge checking';
  el.textContent = '🎙️ …';
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), timeout);
    const resp = await fetch(base + '/api/voice/health', { signal: ctrl.signal });
    clearTimeout(timer);
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    el.className = 'voice-server-badge online';
    el.textContent = '🎙️ Voix neurale';
    el.title = 'Serveur vocal Piper connecté — voix neuronale offline';
  } catch (e) {
    el.className = 'voice-server-badge offline';
    el.textContent = '🎙️ Voix navigateur';
    el.title = 'Serveur vocal non détecté — voix du navigateur (fallback)';
  }
}

function showScreen(name, opts) {
  // Gestion de la pile de navigation (sauf si goBack() dépile avec skipPush)
  const skipPush = opts && opts.skipPush;
  if (!skipPush && currentScreen && currentScreen !== name) {
    navigationStack.push(currentScreen);
    // Limiter la pile pour éviter une croissance infinie
    if (navigationStack.length > 20) navigationStack.shift();
  }
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const el = document.getElementById('screen-' + name);
  if (el) el.classList.add('active');
  currentScreen = name;
  document.getElementById('bottomNav').style.display = (name === 'splash') ? 'none' : 'flex';
  document.querySelectorAll('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.screen === name));
  // La flèche de retour s'affiche sauf sur splash et resonance (qui ont leur propre nav)
  updateBackArrow(name);
  if (name === 'history') renderHistory();
  if (name === 'vitals') renderVitals();
  if (name === 'patients') renderPatients();
  if (name === 'resonance') refreshPatientSelect();
  if (name === 'dossier') updateDossier();
  if (name === 'ia') { initAI(); updateVoiceServerBadge(); }
  if (name === 'splash') updateDashboard();
}

// ── Dashboard "Ma journée" (écran splash contextuel) ──
function updateDashboard() {
  const dateEl = document.getElementById('dashboardDate');
  if (dateEl) dateEl.textContent = new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });

  const pts = loadPatients();
  const keys = Object.keys(pts);
  const setNum = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
  setNum('dashPatientCount', keys.length);

  // Diags aujourd'hui
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  let diagToday = 0, urgentCount = 0;
  let lastDiag = null;
  for (const d of diagnosticHistory) {
    const dDate = new Date(d.date);
    if (dDate >= today) diagToday++;
    if (d.urgent && diagnosticHistory.indexOf(d) < 10) urgentCount++;
    if (!lastDiag && dDate >= today) lastDiag = d;
  }
  setNum('dashDiagToday', diagToday);
  setNum('dashUrgentCount', urgentCount);

  const lastDiagEl = document.getElementById('dashLastDiag');
  if (lastDiagEl) {
    if (lastDiag) {
      lastDiagEl.textContent = 'Dernier diagnostic : ' + lastDiag.diagnosis + ' (' + lastDiag.score + '%)' + (lastDiag.patient ? ' — ' + lastDiag.patient : '');
    } else if (diagnosticHistory.length > 0) {
      const last = diagnosticHistory[0];
      lastDiagEl.textContent = 'Dernier diagnostic : ' + last.diagnosis + ' (' + last.score + '%) — ' + new Date(last.date).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }) + (last.patient ? ' — ' + last.patient : '');
    } else {
      lastDiagEl.textContent = 'Aucun diagnostic aujourd\'hui. Lancez votre première analyse.';
    }
  }
}

// ── Bouton retour (flèche ← + bouton physique Android) ──
function updateBackArrow(name) {
  const arrow = document.getElementById('backArrow');
  if (!arrow) return;
  // Masqué sur splash (point de sortie) et resonance (écran principal de diag)
  const hidden = (name === 'splash' || name === 'resonance');
  arrow.style.display = hidden ? 'none' : 'flex';
}

function goBack() {
  if (navigationStack.length > 0) {
    const prev = navigationStack.pop();
    showScreen(prev, { skipPush: true });
  } else if (currentScreen !== 'splash') {
    showScreen('splash', { skipPush: true });
  } else {
    // Déjà sur splash + pile vide → quitter l'app (mode natif Android)
    if (typeof VITAL_KA_CONFIG !== 'undefined' &&
        VITAL_KA_CONFIG.platform && VITAL_KA_CONFIG.platform.isNative) {
      try {
        const App = window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.App;
        if (App && App.exitApp) App.exitApp();
      } catch (e) { /* ignore — fallback: rester sur splash */ }
    }
  }
}

// Abonnement au bouton physique retour Android (mode natif uniquement)
function setupAndroidBackButton() {
  if (typeof VITAL_KA_CONFIG === 'undefined' ||
      !VITAL_KA_CONFIG.platform || !VITAL_KA_CONFIG.platform.isNative) return;
  try {
    const App = window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.App;
    if (App && App.addListener) {
      App.addListener('backButton', () => goBack());
    }
  } catch (e) { /* ignore */ }
}

// ═══ DIAGNOSTIC ═══

// Réinitialise le formulaire pour un nouveau diagnostic.
// ATTENTION : ne PAS toucher à patientGender (attente utilisateur explicite :
// on conserve le choix Homme/Femme entre deux diagnostics).
function resetDiagnosticForm() {
  const fields = ['symptomsInput', 'patientAge',
    'vitalMuac', 'vitalFR', 'vitalTemp', 'vitalTASyst', 'vitalTADiast',
    'vitalPoids', 'vitalSurface'];
  for (const id of fields) {
    const el = document.getElementById(id);
    if (el) el.value = '';
  }
  const results = document.getElementById('resultsArea');
  if (results) results.innerHTML = '';
  // Réinitialise l'état partagé de l'IA pour qu'elle ne commente plus l'ancien diag
  lastDiagnosisData = null;
  askedQuestions = [];
  pendingClarification = false;
  // Le bouton redevient "LANCER LE DIAGNOSTIC", branché sur diagnose()
  const btn = document.getElementById('diagnoseBtn');
  if (btn) {
    btn.textContent = '🔍 Lancer le diagnostic';
    btn.disabled = false;
    btn.onclick = diagnose;
  }
  // Masque le bouton d'export (lié à un diagnostic/patient)
  const eb = document.getElementById('exportDiagBtn');
  if (eb) eb.style.display = 'none';
}

// Gestionnaire du bouton : bascule entre "lancer" et "nouveau diagnostic".
// Après un diag, le bouton passe en mode reset au prochain clic.
function handleDiagnoseBtn() {
  const btn = document.getElementById('diagnoseBtn');
  if (btn && btn.dataset.mode === 'reset') {
    resetDiagnosticForm();
    return;
  }
  diagnose();
}

async function diagnose() {
  const text = document.getElementById('symptomsInput').value.trim();
  if (!text) return null;
  const btn = document.getElementById('diagnoseBtn');
  btn.disabled = true;
  btn.textContent = 'Analyse en cours...';
  document.getElementById('resultsArea').innerHTML = '<div class="spinner"></div>';

  // Charge la base fusionnée (DB dur + JSON). Fallback offline intégré dans ensureDB().
  if (typeof ensureDB === 'function') {
    try { await ensureDB(); } catch (e) { console.warn('[diagnose] ensureDB failed, using DB dur', e); }
  }

  // Charge la base de connaissances (phyto, protocoles) si pas déjà fait
  if (typeof Knowledge !== 'undefined' && typeof Knowledge.init === 'function') {
    try { await Knowledge.init(); } catch (e) { /* silencieux — phyto optionnelle */ }
  }

  const pVec = encodeSympt(text);
  if (currentPatient && currentPatient.history) {
    for (const past of currentPatient.history.slice(-5)) {
      const pv = encodeSympt(past);
      for (const f of F) if ((pv[f] || 0) > 0) pVec[f] = (pVec[f] || 0) + 0.15;
    }
  }

  const scores = [];
  const activeDB = (typeof getDB === 'function') ? getDB() : DB;
  for (const [n, d] of Object.entries(activeDB)) {
    const v = (typeof getVector === 'function') ? getVector(n) : encodeSympt(d.s.join(' '));
    scores.push({ name: n, score: cosineSim(pVec, v), ...d });
  }

  // ── Règles de seuils : boostent le score cosine quand les critères cliniques sont atteints ──
  if (typeof evaluateRules === 'function' && typeof readPatientData === 'function') {
    const symptomTokens = Object.keys(pVec).filter(k => (pVec[k] || 0) > 0);
    const ruleScores = evaluateRules(readPatientData(symptomTokens), activeDB);
    for (const s of scores) {
      if (ruleScores[s.name] && ruleScores[s.name] > s.score) {
        s.score = ruleScores[s.name];
      }
    }
  }

  scores.sort((a, b) => b.score - a.score);
  const top = scores[0];

  // Résultat complet en mémoire (conduite, délai, différentiels) pour l'IA
	  lastDiagnosisData = { top, scores, symptoms: text, date: new Date().toISOString(), patientId: currentPatient ? currentPatient.id : null, pVec };
  askedQuestions = [];
  pendingClarification = false;

  let h = '';
  if (top.u && top.score > 0.5) {
    h += '<div style="text-align:center;margin-bottom:12px"><span class="badge-urgent">🚨 URGENCE VITALE — ' + top.name + '</span></div>';
  }

  for (const r of scores.slice(0, 5)) {
    const c = r.score > 0.8 ? 'high' : r.score > 0.5 ? 'med' : 'low';
    const cl = r.score > 0.8 ? 'Très élevée' : r.score > 0.5 ? 'Élevée' : 'Modérée';
    const ug = (r.u && r.score > 0.5) ? ' urgent' : '';
    h += '<div class="result-item' + ug + '">';
    h += '<div style="display:flex;justify-content:space-between"><strong>' + (r.u && r.score > 0.5 ? '🚨 ' : '') + r.name + '</strong><span style="font-size:.8em;color:var(--muted)">' + (r.score * 100).toFixed(1) + '% — ' + cl + '</span></div>';
    h += '<div class="conf-bar"><div class="conf-fill ' + c + '" style="width:' + Math.round(r.score * 100) + '%"></div></div>';
    h += '<div class="label-sm">' + r.g + ' | ' + r.d + '</div>';
    h += '<div style="margin-top:8px;padding:12px;background:var(--surface-container-lowest);border-radius:8px;border-left:3px solid var(--accent2);font-size:14px">▶ ' + r.c + '</div>';
    h += '</div>';
  }

  // ═══ Encadré phytothérapie complémentaire (Phase B/C) ═══
  // Les plantes n'entrent JAMAIS dans le score. Affichées à titre informatif.
  h += buildPhytoBox(scores.slice(0, 3), pVec);

  // ═══ Sauvegarde — TOUJOURS, même sans patient sélectionné ═══
  if (top && top.score > 0.4) {
    diagnosticHistory.unshift({
      date: new Date().toISOString(), symptoms: text, diagnosis: top.name,
      score: (top.score * 100).toFixed(0), urgent: top.u,
      gravity: top.g, delay: top.d, advice: top.c,
      patient: currentPatient ? currentPatient.name : null
    });
    if (diagnosticHistory.length > 50) diagnosticHistory = diagnosticHistory.slice(0, 50);
    localStorage.setItem('vital_ka_history', JSON.stringify(diagnosticHistory));

    // Historique du dossier patient (si un patient est sélectionné)
    if (currentPatient) {
      const pts = loadPatients();
      if (pts[currentPatient.id]) {
        if (!pts[currentPatient.id].history) pts[currentPatient.id].history = [];
        pts[currentPatient.id].history.push(top.name + ' (' + (top.score * 100).toFixed(0) + '%)');
        if (pts[currentPatient.id].history.length > 20) pts[currentPatient.id].history = pts[currentPatient.id].history.slice(-20);
        savePatients(pts);
        currentPatient = { id: currentPatient.id, ...pts[currentPatient.id] };
      }
    }
  }

  h += '<p class="footer-note">AIDE AU DIAGNOSTIC — NE REMPLACE PAS UN MÉDECIN</p>';
  h += '<button class="btn btn-secondary ka-voice-btn" style="margin-top:8px" onclick="speakDiagnosisResult(this)">🔊 Écouter le diagnostic</button>';
  h += '<button class="btn btn-primary" style="margin-top:8px" onclick="prescribeMedications()" id="prescribeBtn">📋 Prescrire une ordonnance</button>';

  // ═══ Complément holographique OFFLINE (routeur spectral embarqué) ═══
  // Les 15 hologrammes médicaux (62K faits) sont embarqués dans l'APK —
  // aucun serveur requis. Si le bundle est absent, rien n'est affiché.
  try {
    if (typeof KA_HOLOGRAM !== 'undefined') {
      const ok = await KA_HOLOGRAM.load();
      if (ok) {
        const hol = KA_HOLOGRAM.query(text, 4);
        if (hol && hol.bestScore > 0.15 && hol.results.length) {
          h += KA_HOLOGRAM.renderHTML(hol.results);
        }
      }
    }
  } catch (e) { /* silencieux — hologrammes optionnels */ }

  document.getElementById('resultsArea').innerHTML = h;
  btn.disabled = false;
  // Le bouton bascule en mode "Nouveau diagnostic" → reset au prochain clic
  btn.textContent = '🔄 Nouveau diagnostic';
  btn.dataset.mode = 'reset';

  const eb = document.getElementById('exportDiagBtn');
  if (eb && currentPatient) eb.style.display = 'block';
  return top;
}

// ═══ Encadré phytothérapie complémentaire ═══
// Déterministe : lit Knowledge._phyto via getPhytoFor(). Jamais dans le score.
// Désactivable via localStorage 'vital_ka_phyto_off' (préférence soignant).
// Si patientVector fourni → calcul de RÉSONANCE THÉRAPEUTIQUE (cosineSim).
function buildPhytoBox(topResults, patientVector) {
  if (localStorage.getItem('vital_ka_phyto_off') === '1') return '';
  if (typeof Knowledge === 'undefined' || !Knowledge.getPhytoFor) return '';
  const names = topResults.filter(r => r && r.name && r.score > 0.35).map(r => r.name);
  if (!names.length) return '';
  const plants = Knowledge.getPhytoFor(names, patientVector || null);
  if (!plants.length) return '';
  const GRADE = { A: {cls:'phyto-grade-a', txt:'Preuve clinique'}, B: {cls:'phyto-grade-b', txt:'Évidence préliminaire'}, C: {cls:'phyto-grade-c', txt:'Usage traditionnel'} };
  const hasResonance = plants.some(p => p._resonance > 0);
  let rows = '';
  for (const p of plants.slice(0, 6)) {
    const g = GRADE[p.grade_evidence] || GRADE.C;
    const vigilance = p.niveau_recommandation === 'vigilance';
    const cls = vigilance ? 'phyto-grade-vigilance' : g.cls;
    const local = (p.noms_locaux && p.noms_locaux.length) ? ' · ' + p.noms_locaux.slice(0, 2).join(', ') : '';
    rows += '<div class="phyto-plant' + (vigilance ? ' phyto-plant-alert' : '') + '">';
    rows += '<div style="display:flex;justify-content:space-between;gap:8px;align-items:baseline">';
    rows += '<strong>' + (vigilance ? '⚠️ ' : '🌿 ') + p.nom_scientifique + '</strong>';
    // Badge grade + résonance
    rows += '<span class="phyto-grade ' + cls + '" title="' + g.txt + '">Grade ' + p.grade_evidence + '</span>';
    if (hasResonance && p._resonance > 0) {
      const rPct = Math.round(p._resonance * 100);
      rows += '<span style="font-size:10px;color:var(--muted)" title="Résonance thérapeutique">⚡' + rPct + '%</span>';
    }
    rows += '</div>';
    rows += '<div class="phyto-meta">' + p.indications_label + local + '</div>';
    // Barre de résonance
    if (hasResonance && p._resonance > 0.1) {
      const rPct = Math.round(p._resonance * 100);
      rows += '<div style="margin-top:3px;height:4px;background:rgba(212,168,83,0.15);border-radius:2px"><div style="height:4px;width:' + rPct + '%;background:rgba(212,168,83,0.7);border-radius:2px"></div></div>';
    }
    rows += '<div class="phyto-detail">' + p.partie_utilisee + ' · ' + p.preparation + '</div>';
    if (p.precautions) rows += '<div class="phyto-precaution">' + (vigilance ? '⛔ ' : '⚠️ ') + p.precautions + '</div>';
    if (p.source) rows += '<div class="phyto-source">' + p.source + '</div>';
    rows += '</div>';
  }
  return '<div class="phyto-box">'
    + '<div class="phyto-header">🌿 Phytothérapie complémentaire (tradition africaine)' + (hasResonance ? ' — ⚡ résonance thérapeutique' : '') + '</div>'
    + '<div class="phyto-warning">⚠️ Information à titre indicatif — ne remplace pas le traitement de référence. Respecter les contre-indications et l\'avis d\'un professionnel.</div>'
    + rows
    + '</div>';
}

// ═══ HISTORY ═══
function renderHistory() {
  const el = document.getElementById('historyList');
  if (!el) return;
  if (!diagnosticHistory.length) { el.innerHTML = '<div class="card"><p style="text-align:center;color:var(--muted)">Aucun diagnostic.</p></div>'; return; }
  let h = '';
  for (const d of diagnosticHistory.slice(0, 20)) {
    const dt = new Date(d.date);
    h += '<div class="history-item' + (d.urgent ? ' urgent' : '') + '"><div class="date">' + dt.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) + ' · 👤 ' + (d.patient ? KA_SECURE.escapeHtml(d.patient) : 'Anonyme') + '</div><strong>' + KA_SECURE.escapeHtml(d.diagnosis) + '</strong> <span style="color:var(--accent);font-weight:700">' + KA_SECURE.escapeHtml(d.score) + '%</span><div style="font-size:13px;color:var(--on-surface-variant);margin-top:4px">' + KA_SECURE.escapeHtml(d.symptoms.substring(0, 80)) + '</div></div>';
  }
  el.innerHTML = h;
}

// ═══ VITALS ═══
function renderVitals() {
  const el = document.getElementById('vitalsContent');
  if (!el) return;
  const hr = 68 + Math.floor(Math.random() * 10), spo2 = 96 + Math.floor(Math.random() * 4),
    temp = (36.3 + Math.random() * 1.2).toFixed(1), bp = (110 + Math.floor(Math.random() * 20)) + '/' + (70 + Math.floor(Math.random() * 15));
  el.innerHTML = '<div class="card"><div style="display:flex;align-items:center;gap:8px;margin-bottom:12px"><span class="material-symbols-outlined">monitor_heart</span><h3>Constantes Vitales</h3></div><div class="vital-grid"><div class="vital-card"><div class="value">' + hr + '</div><div class="label">BPM — Cardiaque</div></div><div class="vital-card"><div class="value">' + bp + '</div><div class="label">mmHg — Tension</div></div><div class="vital-card"><div class="value">' + spo2 + '%</div><div class="label">SpO2 — Oxygène</div></div><div class="vital-card"><div class="value">' + temp + '°C</div><div class="label">Température</div></div></div><div style="margin-top:12px"><button class="btn btn-sm" onclick="KA_BLE.startScan()">🔍 Scanner BLE</button><span id="bleStatus" style="font-size:10px;color:var(--outline);margin-left:8px"></span></div><div id="bleVitals"></div></div>';
}

// ═══ PATIENTS ═══
function renderPatients() {
  const el = document.getElementById('patientsList');
  if (!el) return;
  const pts = loadPatients();
  const keys = Object.keys(pts);
  // ── Formulaire de création (profil complet, repliable) ──
  let h = '<details style="margin-bottom:12px;background:var(--surface-container-lowest);border:1px solid var(--border);border-radius:12px;padding:0;overflow:hidden"><summary style="cursor:pointer;color:var(--accent);font-weight:600;padding:14px 16px;font-size:14px"><span class="material-symbols-outlined" style="font-size:18px;vertical-align:-3px">person_add</span> Nouveau patient</summary><div style="padding:12px 16px;display:grid;grid-template-columns:1fr 1fr;gap:8px">'
    + _patientField('Nom complet', 'newPatientName', 'text', '', '2 / span 1')
    + _patientField('Âge', 'newPatientAge', 'number', '', '1')
    + _patientField('Téléphone', 'newPatientPhone', 'tel', '', '1')
    + '<label style="font-size:11px;color:var(--muted)">Sexe<select id="newPatientGender" style="width:100%;background:#141414;color:#d4c8a0;border:1px solid #2a2a2a;padding:8px;border-radius:6px;font-size:13px;font-family:inherit"><option value="">—</option><option value="homme">Homme</option><option value="femme">Femme</option></select></label>'
    + '<label style="font-size:11px;color:var(--muted)">Groupe sanguin<select id="newPatientBlood" style="width:100%;background:#141414;color:#d4c8a0;border:1px solid #2a2a2a;padding:8px;border-radius:6px;font-size:13px;font-family:inherit"><option value="">—</option><option>O+</option><option>O-</option><option>A+</option><option>A-</option><option>B+</option><option>B-</option><option>AB+</option><option>AB-</option></select></label>'
    + _patientField('Poids (kg)', 'newPatientWeight', 'number', '', '1')
    + _patientField('Allergies', 'newPatientAllergies', 'text', 'ex: pénicilline', '2 / span 1')
    + '<div style="grid-column:1 / -1;margin-top:4px"><button class="btn btn-sm btn-primary" style="width:100%" onclick="addPatient()">➕ Créer le dossier</button></div>'
    + '</div></details>';
  if (!keys.length) h += '<div class="card"><p style="text-align:center;color:var(--muted)">Aucun patient. Créez un premier dossier ci-dessus.</p></div>';
  for (let i = keys.length - 1; i >= Math.max(0, keys.length - 10); i--) {
    const id = keys[i], p = pts[id];
    const sc = p.shortCode ? '<span style="font-size:10px;color:var(--muted);background:rgba(212,168,83,.1);padding:1px 5px;border-radius:4px">code ' + KA_SECURE.escapeHtml(p.shortCode) + '</span>' : '';
    const sub = [p.age ? p.age + ' ans' : '', p.gender === 'homme' ? 'H' : p.gender === 'femme' ? 'F' : '', (p.history ? p.history.length : 0) + ' diags'].filter(Boolean).join(' · ');
    h += '<div class="patient-row" onclick="selectPatient(\'' + id + '\')"><div class="avatar">' + KA_SECURE.escapeHtml((p.name || '?')[0].toUpperCase()) + '</div><div class="info"><div class="name">' + KA_SECURE.escapeHtml(p.name) + ' ' + sc + '</div><div class="meta">' + sub + '</div></div><span class="material-symbols-outlined">chevron_right</span></div>';
  }
  el.innerHTML = h;
}

// Helper : champ de formulaire label+input stylé
function _patientField(label, id, type, ph, span) {
  return '<label style="font-size:11px;color:var(--muted);grid-column:' + (span || '1') + '">' + label + '<input id="' + id + '" type="' + type + '" placeholder="' + (ph || '') + '" style="width:100%;background:#141414;color:#d4c8a0;border:1px solid #2a2a2a;padding:8px;border-radius:6px;font-size:13px;font-family:inherit;margin-top:2px"></label>';
}

// Sélection d'un patient (depuis la liste) → ouvre le diagnostic
function selectPatient(id) {
  const pts = loadPatients();
  currentPatient = id && pts[id] ? { id, ...pts[id] } : null;
  showScreen('resonance');
  refreshPatientSelect();
  // Pré-remplit le sexe du patient dans la barre de diagnostic
  if (currentPatient && currentPatient.gender) {
    const gs = document.getElementById('patientGender');
    if (gs) gs.value = currentPatient.gender;
  }
}

function addPatient() {
  const name = (document.getElementById('newPatientName')?.value || '').trim();
  if (!name) { alert('Le nom du patient est obligatoire.'); return; }
  const age = (document.getElementById('newPatientAge')?.value || '').trim();
  const gender = (document.getElementById('newPatientGender')?.value || '').trim();
  const blood = (document.getElementById('newPatientBlood')?.value || '').trim();
  const weight = (document.getElementById('newPatientWeight')?.value || '').trim();
  const phone = (document.getElementById('newPatientPhone')?.value || '').trim();
  const allergies = (document.getElementById('newPatientAllergies')?.value || '').trim();
  const pts = loadPatients();
  const id = 'p' + Date.now();
  pts[id] = {
    id, name, age, gender, blood, weight, phone,
    allergies: allergies ? allergies.split(/[,;]+/).map(s => s.trim()).filter(Boolean) : [],
    shortCode: generateShortCode(id),
    history: [],
    createdAt: new Date().toISOString(),
  };
  savePatients(pts);
  // Vide le formulaire
  ['newPatientName', 'newPatientAge', 'newPatientPhone', 'newPatientWeight', 'newPatientAllergies'].forEach(fid => {
    const el = document.getElementById(fid); if (el) el.value = '';
  });
  ['newPatientGender', 'newPatientBlood'].forEach(fid => {
    const el = document.getElementById(fid); if (el) el.value = '';
  });
  renderPatients();
  refreshPatientSelect();
  // Sélectionne automatiquement le nouveau patient
  selectPatient(id);
}

// ═══ BRIDGE ═══

// Identification d'un patient par son code court (6 caractères).
// Cherche dans les patients locaux ; si non trouvé, tente un transfert long.
function lookupPatientByCode() {
  const input = document.getElementById('patientCodeInput');
  const result = document.getElementById('lookupResult');
  if (!input) return;
  const code = input.value.trim().toUpperCase();
  if (!code) {
    if (result) result.innerHTML = '<span style="color:#d4a853">⌨️ Saisissez un code.</span>';
    return;
  }
  // Normalisation : retire les tirets/espaces pour la comparaison
  const norm = code.replace(/[\s-]/g, '');
  const pts = loadPatients();
  // 1. Recherche par code court local
  let found = null;
  for (const [id, p] of Object.entries(pts)) {
    const sc = (p.shortCode || '').replace(/[\s-]/g, '');
    if (sc && sc === norm) { found = { id, ...p }; break; }
  }
  if (found) {
    if (result) result.innerHTML = '<span style="color:#4ade80">✅ ' + KA_SECURE.escapeHtml(found.name) + ' trouvé</span>';
    selectPatient(found.id);
    setTimeout(() => showScreen('dossier'), 600);
    input.value = '';
    return;
  }
  // 2. Tente un transfert long (code de transfert KA Bridge)
  const decoded = (typeof KA_BRIDGE !== 'undefined' && KA_BRIDGE.decode) ? KA_BRIDGE.decode(code) : null;
  if (decoded) {
    if (result) result.innerHTML = '<span style="color:#4ade80">✅ Dossier importé</span>';
    const newId = KA_BRIDGE.importToKACare(decoded);
    if (newId) {
      selectPatient(newId);
      setTimeout(() => showScreen('dossier'), 600);
      input.value = '';
      return;
    }
  }
  // 3. Non trouvé
  if (result) result.innerHTML = '<span style="color:#f87171">❌ Aucun patient pour le code « ' + KA_SECURE.escapeHtml(code) + ' »</span>';
}
function importPatientData() {
  KA_BRIDGE.readTransferCode(function (pkg) {
    const id = KA_BRIDGE.importToKACare(pkg);
    if (id) { alert('Patient importé !'); renderPatients(); refreshPatientSelect(); }
    else { alert('Format invalide.'); }
  });
}
function exportDiagnosis() {
  if (!currentPatient) { alert('Sélectionnez un patient d\'abord.'); return; }
  const diag = { diagnostic_principal: { maladie: '', score: 0, symptomes_attendus: [], conduite: '', urgence: false, delai: '' }, diagnostics_différentiels: [] };
  const last = getLastDiagnosis();
  if (last && last.top) {
    diag.diagnostic_principal.maladie = last.top.name;
    diag.diagnostic_principal.score = Math.round((last.top.score || 0) * 100);
    diag.diagnostic_principal.conduite = last.top.c || '';
    diag.diagnostic_principal.urgence = !!last.top.u;
    diag.diagnostic_principal.delai = last.top.d || '';
    diag.diagnostics_différentiels = (last.scores || []).slice(1, 4).map(s => ({ maladie: s.name, score: Math.round((s.score || 0) * 100) }));
  }
  if (!diag.diagnostic_principal.maladie) {
    const results = document.getElementById('resultsArea');
    if (results) {
      const first = results.querySelector('.result-item strong');
      if (first) diag.diagnostic_principal.maladie = first.textContent.replace('🚨', '').trim();
    }
  }
  if (!diag.diagnostic_principal.maladie) { alert('Lancez un diagnostic d\'abord.'); return; }
  const pkg = KA_BRIDGE.doctorToPatient(diag, { name: currentPatient.name, id: currentPatient.id });
  const modal = document.createElement('div');
  modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.9);z-index:200;display:flex;align-items:center;justify-content:center;padding:20px';
  modal.innerHTML = '<div style="background:#1a1a1a;border:1px solid #d4a853;border-radius:16px;padding:24px;max-width:400px;text-align:center"><h3>📤 Transfert au patient</h3><div id="qrTransfer" style="margin:12px 0"></div><p style="font-size:.7em;color:#9b8f7e">Le patient scanne ce code avec KA Patient</p><button onclick="this.parentElement.parentElement.remove()" style="background:#d4a853;color:#0d0d0d;border:none;padding:10px 24px;border-radius:8px;cursor:pointer;margin-top:12px;font-weight:700;font-family:inherit">Fermer</button></div>';
  document.body.appendChild(modal);
  modal.onclick = function (e) { if (e.target === modal) modal.remove(); };
  KA_BRIDGE.generateQRCode ? KA_BRIDGE.generateQRCode(pkg, 'qrTransfer') : null;
}

// ═══ ORDONNANCE — Prescription → QR code → Pharmacien ═══
function prescribeMedications() {
  if (!currentPatient) { alert('Sélectionnez un patient d\'abord.'); return; }
  const last = getLastDiagnosis();
  if (!last || !last.top) { alert('Lancez un diagnostic d\'abord.'); return; }

  const modal = document.createElement('div');
  modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.92);z-index:200;overflow-y:auto;padding:20px';
  const doctorName = localStorage.getItem('vital_ka_doctor_name') || 'Dr Soignant';
  modal.innerHTML = '<div style="background:#1a1a1a;border:1px solid #d4a853;border-radius:20px;padding:24px;max-width:500px;margin:20px auto;color:#eae1d7;font-family:Inter,sans-serif">'
    + '<h2 style="color:#d4a853;text-align:center;margin-bottom:4px">📋 Ordonnance Médicale</h2>'
    + '<p style="text-align:center;color:#9b8f7e;font-size:12px;margin-bottom:16px">' + KA_SECURE.escapeHtml(doctorName) + ' · ' + new Date().toLocaleDateString('fr-FR',{day:'numeric',month:'long',year:'numeric'}) + '</p>'
    + '<div style="background:rgba(212,168,83,.08);border-radius:12px;padding:12px;margin-bottom:12px">'
    + '<div style="font-size:11px;color:#9b8f7e;text-transform:uppercase">Patient</div>'
    + '<div style="font-weight:700">' + KA_SECURE.escapeHtml(currentPatient.name) + ' · ' + (currentPatient.age||'?') + ' ans · ' + (currentPatient.gender||'?') + '</div>'
    + '<div style="font-size:11px;color:#9b8f7e;margin-top:4px">Diagnostic : ' + KA_SECURE.escapeHtml(last.top.name) + ' (' + Math.round(last.top.score*100) + '%)</div>'
    + '</div>'
    + '<div id="rxMeds" style="margin-bottom:12px">'
    + '<div class="rx-row" style="display:flex;gap:8px;align-items:center;margin-bottom:6px"><input class="rx-name" placeholder="Médicament" style="flex:2"><input class="rx-dose" placeholder="Dosage" style="flex:1"><input class="rx-dur" placeholder="Durée" style="flex:1"><button class="rx-remove btn btn-secondary" style="width:auto;padding:8px 12px;font-size:12px" onclick="this.parentElement.remove()">×</button></div>'
    + '</div>'
    + '<button class="btn btn-secondary" style="width:auto;padding:8px 16px;font-size:12px;margin-bottom:16px" onclick="var r=document.createElement(\'div\');r.className=\'rx-row\';r.style.cssText=\'display:flex;gap:8px;align-items:center;margin-bottom:6px\';r.innerHTML=\'<input class=rx-name placeholder=Médicament style=flex:2><input class=rx-dose placeholder=Dosage style=flex:1><input class=rx-dur placeholder=Durée style=flex:1><button class=\"rx-remove btn btn-secondary\" style=\"width:auto;padding:8px 12px;font-size:12px\" onclick=this.parentElement.remove()>×</button>\';document.getElementById(\'rxMeds\').appendChild(r)">➕ Ajouter un médicament</button>'
    + '<div style="margin-bottom:12px"><textarea id="rxNotes" placeholder="Notes complémentaires..." style="width:100%;min-height:50px;background:rgba(15,15,25,.8);color:#eae1d7;border:1px solid #2a2a2a;border-radius:10px;padding:10px;font-family:inherit;font-size:13px"></textarea></div>'
    + '<button class="btn btn-primary" onclick="finalizePrescription(this)" style="margin-bottom:8px">📤 Générer l\'ordonnance + QR code</button>'
    + '<button class="btn btn-secondary" style="margin-top:8px" onclick="prescribeLabAnalysis()">🧪 Prescrire une analyse (laboratoire)</button>'
    + '<div id="rxQR" style="text-align:center;margin-top:12px"></div>'
    + '<button class="btn btn-secondary" style="margin-top:8px" onclick="this.closest(\'div\').parentElement.parentElement.remove()">Fermer</button>'
    + '</div>';
  document.body.appendChild(modal);
  modal.onclick = function(e) { if (e.target === modal) modal.remove(); };
}

// ═══ PRESCRIRE UNE ANALYSE (Médecin → Laboratoire) ═══
function prescribeLabAnalysis() {
  if (!currentPatient) { alert('Sélectionnez un patient d\'abord.'); return; }
  const last = getLastDiagnosis();
  const doctorName = localStorage.getItem('vital_ka_doctor_name') || 'Dr Soignant';

  // Modale de sélection des analyses
  const modal = document.createElement('div');
  modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.92);z-index:210;overflow-y:auto;padding:20px';
  const ANALYSES_COMMUNES = ['NFS (Numération formule sanguine)', 'Glycémie à jeun', 'TDR Paludisme', 'Goutte épaisse',
    'Test de Grossesse', 'CRP', 'Bilan hépatique', 'Bilan rénal', 'Test VIH', 'Test TB (GeneXpert)',
    'ECBU (Examen cytobactériologique des urines)', 'Selles (parasitologie)', 'Groupe sanguin + Rhésus', 'Ferritine', 'Hémoglobine'];
  modal.innerHTML = '<div style="background:#1a1a1a;border:1px solid #d4a853;border-radius:20px;padding:24px;max-width:500px;margin:20px auto;color:#eae1d7;font-family:Inter,sans-serif">'
    + '<h2 style="color:#d4a853;text-align:center;margin-bottom:4px">🧪 Ordonnance d\'analyse</h2>'
    + '<p style="text-align:center;color:#9b8f7e;font-size:12px;margin-bottom:16px">' + KA_SECURE.escapeHtml(doctorName) + ' · ' + KA_SECURE.escapeHtml(currentPatient.name) + ' · ' + (currentPatient.age || '?') + ' ans</p>'
    + '<div style="margin-bottom:12px" id="labChecks">'
    + ANALYSES_COMMUNES.map((a, i) => '<label style="display:flex;align-items:center;gap:8px;padding:6px 0;font-size:13px;cursor:pointer"><input type="checkbox" class="lab-check" value="' + KA_SECURE.escapeHtml(a) + '" ' + (i < 3 ? 'checked' : '') + ' style="width:auto">' + KA_SECURE.escapeHtml(a) + '</label>').join('')
    + '</div>'
    + '<div style="margin-bottom:12px"><input id="labCustom" placeholder="Autre analyse (optionnel)..." style="width:100%;background:rgba(15,15,25,.8);color:#eae1d7;border:1px solid #2a2a2a;border-radius:10px;padding:10px;font-family:inherit;font-size:13px"></div>'
    + '<button class="btn btn-primary" onclick="finalizeLabOrder(this)" style="margin-bottom:8px">📤 Générer le QR analyse</button>'
    + '<div id="labQR" style="text-align:center;margin-top:12px"></div>'
    + '<button class="btn btn-secondary" style="margin-top:8px" onclick="this.closest(\'div\').parentElement.parentElement.remove()">Fermer</button>'
    + '</div>';
  document.body.appendChild(modal);
  modal.onclick = function(e) { if (e.target === modal) modal.remove(); };
}

function finalizeLabOrder(btn) {
  if (typeof KA_BRIDGE === 'undefined') { alert('KA_BRIDGE indisponible.'); return; }
  const doctorName = localStorage.getItem('vital_ka_doctor_name') || 'Dr Soignant';
  const checked = [];
  document.querySelectorAll('.lab-check:checked').forEach(c => checked.push(c.value));
  const custom = (document.getElementById('labCustom')?.value || '').trim();
  if (custom) checked.push(custom);
  if (!checked.length) { alert('Sélectionnez au moins une analyse.'); return; }

  const last = getLastDiagnosis();
  const ordonnance = KA_BRIDGE.doctorToLab({
    id: currentPatient.id, name: currentPatient.name, age: currentPatient.age,
    gender: currentPatient.gender, doctor: doctorName
  }, checked, last?.top?.name || '');

  // Stocker localement (récupérable par code court dans le labo)
  const pending = JSON.parse(localStorage.getItem('ka_lab_orders') || '[]');
  pending.push(ordonnance);
  localStorage.setItem('ka_lab_orders', JSON.stringify(pending));

  // Générer le QR
  const code = KA_BRIDGE.encode(ordonnance);
  const qrDiv = document.getElementById('labQR');
  if (qrDiv) {
    qrDiv.innerHTML = '<div style="background:#fff;color:#000;padding:16px;border-radius:12px;word-break:break-all;font-size:11px;max-height:120px;overflow-y:auto;text-align:center">' + code + '</div>' +
      '<p style="font-size:12px;color:#9b8f7e;margin-top:8px">Code court : <b style="color:#d4a853">' + ordonnance.id + '</b></p>' +
      '<button class="btn btn-secondary" style="margin-top:8px" onclick="navigator.clipboard.writeText(\'' + code + '\')">📋 Copier le code</button>' +
      '<p style="font-size:11px;color:#9b8f7e;margin-top:8px">Le laboratoire charge ce code dans « KA Laboratoire » — les résultats seront envoyés automatiquement au dossier du patient.</p>';
  }
  if (typeof KA_PLATFORM !== 'undefined' && KA_PLATFORM.emit) {
    KA_PLATFORM.emit('lab_order', { id: ordonnance.id, patientName: currentPatient.name, nAnalyses: checked.length });
  }
}

function finalizePrescription(btn) {
  const last = getLastDiagnosis();
  if (!last || !currentPatient) return;
  const doctorName = localStorage.getItem('vital_ka_doctor_name') || 'Dr Soignant';
  const meds = [];
  document.querySelectorAll('.rx-row').forEach(row => {
    const name = row.querySelector('.rx-name')?.value?.trim();
    const dose = row.querySelector('.rx-dose')?.value?.trim();
    const dur = row.querySelector('.rx-dur')?.value?.trim();
    if (name) meds.push({ name, dosage: dose, duree: dur });
  });
  const notes = document.getElementById('rxNotes')?.value?.trim() || '';
  const ordonnance = {
    type: 'prescription', version: '1.0',
    id: 'rx_' + Date.now(), date: new Date().toISOString(),
    patient: { id: currentPatient.id, name: currentPatient.name, age: currentPatient.age, gender: currentPatient.gender },
    medecin: { name: doctorName },
    diagnostic: { nom: last.top.name, score: Math.round(last.top.score * 100), conduite: last.top.c || '' },
    medicaments: meds, notes: notes,
  };
  // Sauver dans le dossier patient
  const pts = loadPatients();
  if (pts[currentPatient.id]) {
    if (!pts[currentPatient.id].ordonnances) pts[currentPatient.id].ordonnances = [];
    pts[currentPatient.id].ordonnances.push(ordonnance);
    savePatients(pts);
    currentPatient = { id: currentPatient.id, ...pts[currentPatient.id] };
  }
  // QR code
  const qrDiv = document.getElementById('rxQR');
  if (qrDiv && typeof KA_BRIDGE !== 'undefined' && KA_BRIDGE.generateQRCode) {
    const encoded = KA_BRIDGE.generateTransferCode(ordonnance);
    qrDiv.innerHTML = '<p style="font-size:11px;color:#d4a853;margin-bottom:4px">📱 À scanner par le pharmacien</p><div id="rxQrImg"></div>';
    KA_BRIDGE.generateQRCode(encoded, 'rxQrImg');
  }
  btn.textContent = '✅ Ordonnance générée'; btn.disabled = true;
  updateDossier();
}

// ═══ SECURITY ═══
function setupPIN() {
  const pin = prompt('Créez un code PIN à 4 chiffres :');
  if (!pin || pin.length !== 4 || !/^\d{4}$/.test(pin)) { alert('PIN invalide (4 chiffres requis).'); return; }
  KA_SECURE.setPIN(pin).then(ok => {
    if (ok) { alert('PIN configuré et haché (SHA-256).'); }
    else { alert('Erreur.'); }
  });
}

// ═══ INIT ═══
KA_SECURE.showLockScreen(function () {
  refreshPatientSelect();
  // Quick symptom chips (dans la modale maintenant)
  ['fievre', 'toux', 'fatigue', 'maux de tete', 'douleur thoracique', 'essoufflement', 'nausees', 'diarrhee', 'frissons', 'mal de gorge'].forEach(s => {
    const b = document.createElement('button');
    b.className = 'chip'; b.textContent = s;
    b.onclick = function () {
      this.classList.toggle('active');
      const ta = document.getElementById('symptomsInput');
      const cur = ta.value.split(',').map(x => x.trim()).filter(x => x);
      if (this.classList.contains('active')) { if (!cur.includes(s)) cur.push(s); }
      else { const i = cur.indexOf(s); if (i >= 0) cur.splice(i, 1); }
      ta.value = cur.join(', ');
    };
    document.getElementById('quickChips').appendChild(b);
  });
  // Demo buttons (dans la modale maintenant)
  [['Fievre + toux + anosmie', 'fievre, toux seche, fatigue, anosmie'], ['Douleur thoracique + sueurs', 'douleur thoracique, essoufflement, sueurs froides, nausees'], ['Fievre cyclique + frissons', 'fievre cyclique, frissons, sueurs, maux de tete'], ['Fievre + douleurs articulaires', 'fievre elevee, douleurs articulaires, eruption cutanee']].forEach(([n, t]) => {
    const b = document.createElement('button');
    b.textContent = n; b.className = 'chip';
    b.onclick = () => { document.getElementById('symptomsInput').value = t; diagnose(); closeSymptomsModal(); };
    document.getElementById('demoBtns').appendChild(b);
  });
});

// ═══ Raccourcis clavier (PWA/Desktop) ═══
document.addEventListener('keydown', function(e) {
  // Ignorer si l'utilisateur tape dans un champ de texte
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
  const key = e.key.toLowerCase();
  if (key === 'n') {
    e.preventDefault();
    resetDiagnosticForm();
    showScreen('resonance');
    setTimeout(function() {
      const si = document.getElementById('symptomsInput');
      if (si) si.focus();
    }, 300);
  } else if (key === 'a') {
    e.preventDefault();
    showScreen('ia');
  } else if (key === 'f') {
    e.preventDefault();
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      document.documentElement.requestFullscreen().catch(function() {});
    }
  }
});

function openSymptomsModal() {
  document.getElementById('symptomsModalOverlay').classList.add('open');
}
function closeSymptomsModal() {
  document.getElementById('symptomsModalOverlay').classList.remove('open');
}

// ═══ TELECONSULTATION ═══
let teleMuted = false, teleVideoOn = true;

function initNetworkBar() {
  KA_Network.init().then(status => {
    updateNetworkUI(status);
    // Détecter si le serveur KA local tourne
    KA_Network.detectKAServer().then(url => {
      if (url) {
        const ip = document.getElementById('netIP');
        if (ip) {
          ip.innerHTML = '🟢 Serveur actif — <a href="' + url + '" target="_blank" style="color:#27ae60;text-decoration:underline">Accès patient</a>';
          ip.style.display = 'inline';
        }
      }
    });
  });
  KA_Network.onChange(status => updateNetworkUI(status));
}

function updateNetworkUI(s) {
  const indicator = document.getElementById('netIndicator');
  const label = document.getElementById('netLabel');
  const ip = document.getElementById('netIP');
  if (!indicator || !label) return;
  
  indicator.className = 'net-indicator';
  
  if (!s.online && !s.localIP) {
    indicator.classList.add('offline');
    label.textContent = 'Hors ligne — WiFi requis pour teleconsultation';
    if (ip) ip.style.display = 'none';
  } else if (s.localIP && s.quality === 'local-only') {
    indicator.classList.add('local');
    label.textContent = 'Reseau local — Pret pour P2P direct';
    if (ip) { ip.textContent = s.localIP; ip.style.display = 'inline'; }
  } else if (s.quality === 'excellent' || s.quality === 'good') {
    indicator.classList.add('online');
    label.textContent = 'Connecte — ' + (s.type || 'WiFi') + ' (' + s.quality + ')';
    if (ip && s.localIP) { ip.textContent = s.localIP; ip.style.display = 'inline'; }
  } else if (s.quality === 'slow' || s.quality === 'poor') {
    indicator.classList.add('slow');
    label.textContent = 'Connexion lente — HCV optimise';
    if (ip && s.localIP) { ip.textContent = s.localIP; ip.style.display = 'inline'; }
  }
}

function startTeleconsultation() {
  initNetworkBar();
  KATelemedecine.init('teleLocalVideo', 'teleRemoteCanvas');
  
  // Vérifier la caméra d'abord
  KATelemedecine.checkCamera().then(result => {
    if (!result.ok) {
      document.getElementById('teleStatusText').textContent = 'Camera indisponible';
      document.getElementById('teleStatusSub').textContent = result.error;
      document.getElementById('teleLocalStatus').classList.add('offline');
      return;
    }
    // Aperçu caméra
    KATelemedecine.previewCamera().then(preview => {
      if (preview.ok) {
        document.getElementById('teleLocalStatus').classList.add('live');
        document.getElementById('teleStatusSub').textContent = 'Camera active — Pret pour la consultation';
      }
    });
  });
  
  KATelemedecine.onStateChange = function(status) {
    const txt = document.getElementById('teleStatusText');
    const sub = document.getElementById('teleStatusSub');
    const localStatus = document.getElementById('teleLocalStatus');
    const remoteStatus = document.getElementById('teleRemoteStatus');
    
    localStatus.className = 'video-status';
    remoteStatus.className = 'video-status';
    
    switch (status) {
      case 'calling':
        txt.textContent = 'Appel en cours...';
        sub.textContent = 'Préparation de la connexion sécurisée HCV';
        localStatus.classList.add('ringing');
        break;
      case 'ringing':
        txt.textContent = 'En attente du patient...';
        sub.textContent = 'Le patient doit scanner le QR code';
        localStatus.classList.add('ringing');
        break;
      case 'connected':
        txt.textContent = 'Consultation en cours';
        sub.textContent = 'Connexion sécurisée — Compression HCV active';
        localStatus.classList.add('live');
        remoteStatus.classList.add('live');
        document.getElementById('signalQRContainer').style.display = 'none';
        document.getElementById('signalPromptContainer').style.display = 'none';
        break;
      case 'ended':
        txt.textContent = 'Consultation terminée';
        sub.textContent = 'Prêt pour une nouvelle consultation';
        localStatus.classList.add('ended');
        remoteStatus.classList.add('ended');
        break;
    }
  };
  
  KATelemedecine.onStatsUpdate = function(stats) {
    document.getElementById('hcvSent').textContent = stats.sent;
    document.getElementById('hcvRecv').textContent = stats.received;
    if (stats.sent > 0) {
      const ratio = (stats.bytesSent / (stats.sent * 320 * 240 * 3 / 4)).toFixed(1);
      document.getElementById('hcvRatio').textContent = ratio + 'x';
    }
  };
  
  KATelemedecine.onError = function(msg) {
    document.getElementById('teleStatusText').textContent = 'Erreur';
    document.getElementById('teleStatusSub').textContent = msg;
    alert('Erreur télémédecine : ' + msg);
  };
  
  KATelemedecine.startCall('doctor');
}

function acceptTeleCall() {
  const sdpInput = document.getElementById('sdpInput').value.trim();
  if (!sdpInput) { alert('Collez le code SDP du médecin.'); return; }
  
  KATelemedecine.init('teleLocalVideo', 'teleRemoteCanvas');
  KATelemedecine.onStateChange = function(status) {
    const txt = document.getElementById('teleStatusText');
    if (status === 'connected') {
      txt.textContent = 'Consultation en cours';
      document.getElementById('signalPromptContainer').style.display = 'none';
    }
  };
  KATelemedecine.acceptCall(sdpInput);
}

function toggleTeleMute() {
  const on = KATelemedecine.toggleMute();
  const btn = document.getElementById('btnCallMute');
  if (on) { btn.classList.remove('muted'); btn.querySelector('span').textContent = 'mic'; }
  else { btn.classList.add('muted'); btn.querySelector('span').textContent = 'mic_off'; }
}

function toggleTeleVideo() {
  const on = KATelemedecine.toggleVideo();
  const btn = document.getElementById('btnCallVideo');
  if (on) { btn.classList.remove('off'); btn.querySelector('span').textContent = 'videocam'; }
  else { btn.classList.add('off'); btn.querySelector('span').textContent = 'videocam_off'; }
}

function endTeleconsultation() {
  KATelemedecine.hangUp();
  showScreen('resonance');
}

// ═══ HARMONIC AI ═══
let kaAI = null;
let currentDiagnosisResult = null;
let lastDiagnosisData = null;      // résultat complet du dernier diagnostic {top, scores, symptoms, date, patientId}
let askedQuestions = [];           // questions de clarification déjà posées
let pendingClarification = false;  // une question de clarification attend une réponse

// Garantit que kaAI est initialisé avant tout usage (corrige le TypeError au 1er usage)
async function ensureAI() {
  if (!kaAI) await initAI();
  return kaAI;
}

async function initAI() {
  if (!kaAI) {
    kaAI = new KACareAI();
    kaAI.setSpecialty(localStorage.getItem('vital_ka_specialty') || 'generaliste');
  }
  const mode = await kaAI.init();
  const badge = document.getElementById('aiModeBadge');
  const label = document.getElementById('aiModeLabel');
  if (badge) {
    badge.textContent = mode === 'hybrid' ? 'HYBRID' : 'LOCAL';
    badge.className = 'ai-mode-badge ' + mode;
  }
  if (label) {
    const spec = kaAI.getSpecialty();
    label.textContent = (mode === 'hybrid' ? 'Connecte au serveur harmonique' : 'Mode hors-ligne — Templates deterministes') + ' · ' + spec.icon + ' ' + spec.label;
  }
  initSpecialtySelect();
  initVoiceSelect();
}

// ═══ SPÉCIALISATION MÉDICALE ═══
function initSpecialtySelect() {
  const sel = document.getElementById('specialtySelect');
  if (!sel) return;
  if (!sel.options.length) {
    for (const [id, s] of Object.entries(KACareAI.SPECIALTIES)) {
      const opt = document.createElement('option');
      opt.value = id;
      opt.textContent = s.icon + ' ' + s.label;
      sel.appendChild(opt);
    }
  }
  if (kaAI) sel.value = kaAI.specialty;
}

async function onSpecialtyChange(id) {
  await ensureAI();
  kaAI.setSpecialty(id);
  localStorage.setItem('vital_ka_specialty', id);
  const spec = kaAI.getSpecialty();
  const label = document.getElementById('aiModeLabel');
  if (label) label.textContent = label.textContent.replace(/ · .*$/, '') + ' · ' + spec.icon + ' ' + spec.label;
  aiAddMessage(spec.icon + ' Specialisation active : **' + spec.label + '** — ' + spec.focus + '.', 'system');
}

// ═══ SÉLECTEUR DE VOIX PIPER ═══
function initVoiceSelect() {
  const sel = document.getElementById('voiceSelect');
  if (!sel) return;
  if (sel.options.length) return;
  const cfg = (typeof VITAL_KA_CONFIG !== 'undefined') ? VITAL_KA_CONFIG : null;
  const voices = (cfg && cfg.voice && cfg.voice.availableVoices) || [];
  if (!voices.length) {
    sel.innerHTML = '<option value="fr_FR-siwis-medium">Siwis (F)</option>';
    return;
  }
  for (const v of voices) {
    const opt = document.createElement('option');
    opt.value = v.id;
    opt.textContent = v.label;
    sel.appendChild(opt);
  }
  const active = (cfg && cfg.voice && cfg.voice.active) || 'fr_FR-siwis-medium';
  sel.value = voices.some(v => v.id === active) ? active : 'fr_FR-siwis-medium';
}

function onVoiceChange(voiceId) {
  if (typeof VITAL_KA_CONFIG !== 'undefined' && VITAL_KA_CONFIG.voice) {
    VITAL_KA_CONFIG.voice.active = voiceId;
  }
  const sel = document.getElementById('voiceSelect');
  const opt = sel && sel.selectedOptions[0];
  const label = opt ? opt.textContent : voiceId;
  aiAddMessage('🎙️ Voix active : **' + label + '** — le prochain message vocal utilisera cette voix.', 'system');
  console.log('[VitalKa] Voix changee →', voiceId);
}

function aiAddMessage(text, role) {
  const conv = document.getElementById('aiConversation');
  const div = document.createElement('div');
  div.className = 'ai-message ' + role;
  // Échapper le HTML puis convertir les **gras** et \n
  let safe = KA_SECURE.escapeHtml(text);
  safe = safe.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
  div.innerHTML = safe;
  conv.appendChild(div);
  conv.scrollTop = conv.scrollHeight;
}

async function aiSend() {
  const input = document.getElementById('aiInput');
  const text = input.value.trim();
  if (!text) return;

  aiAddMessage(text, 'user');
  input.value = '';
  await ensureAI(); // kaAI garanti non-null (corrige le TypeError au 1er usage)

  // Réponse à une question de clarification en cours ?
  if (pendingClarification) {
    pendingClarification = false;
    const ta = document.getElementById('symptomsInput');
    const res = kaAI.integrateClarification(text, ta.value);
    if (res.text !== ta.value) {
      ta.value = res.text;
      aiAddMessage('✅ Reponse integree aux symptomes. Relance de l\'analyse...', 'system');
      await diagnose();
      const diag = getLastDiagnosis();
      if (diag) {
	        aiAddMessage(kaAI.explain(diag.top, buildCurrentHologram(), diag.pVec), 'ai');
        aiSuggestClarification(diag);
      }
    } else {
      aiAddMessage('Reponse notee.', 'system');
    }
    return;
  }

  // Analyser la question
  setTimeout(() => {
    const q = text.toLowerCase();
    if (q.includes('explique') || q.includes('diagnostic') || q.includes('pourquoi')) {
      aiQuickExplain();
    } else if (q.includes('différentiel') || q.includes('autre') || q.includes('compar')) {
      aiQuickDifferential();
    } else if (q.includes('hologramme') || q.includes('holo')) {
      aiQuickHolo();
    } else if (q.includes('apprendre') || q.includes('formation') || q.includes('comment')) {
      aiQuickTeach();
    } else {
      kaAI.searchMedical(text).then(answer => {
        aiAddMessage(answer, 'ai');
      });
    }
  }, 400);
}

async function aiQuickExplain() {
  await ensureAI();
  const diag = getLastDiagnosis();
  if (!diag) {
    aiAddMessage('Aucun diagnostic recent. Lancez un diagnostic depuis l\'ecran Resonance d\'abord.', 'system');
    return;
  }
  const holo = buildCurrentHologram();
  const explanation = kaAI.explain(diag.top, holo, diag.pVec);
  aiAddMessage(explanation, 'ai');
  aiSuggestClarification(diag); // boucle de clarification (ex-code mort)
}

async function aiQuickDifferential() {
  await ensureAI();
  const diag = getLastDiagnosis();
  if (!diag || !diag.scores || diag.scores.length < 2) {
    aiAddMessage('Lancez un diagnostic pour voir les diagnostics differentiels.', 'system');
    return;
  }
  const holo = buildCurrentHologram();
  const reasoning = kaAI.reason(diag.scores, holo);
  aiAddMessage(reasoning, 'ai');
}

function aiQuickHolo() {
  const holo = buildCurrentHologram();
  if (!holo || holo.features.length === 0) {
    aiAddMessage('Aucun hologramme disponible. Remplissez les informations patient et symptomes.', 'system');
    return;
  }
  const viz = document.getElementById('holoViz');
  viz.style.display = 'block';
  
  // Afficher les barres de l'hologramme
  const groups = { sym: 0, vit: 0, hx: 0, risk: 0, med: 0, ctx: 0 };
  holo.features.forEach(f => {
    const prefix = f.split('_')[0];
    if (prefix === 'sym') groups.sym++;
    else if (['tachycardia','bradycardia','hr_normal','fever','hypoxia','spo2_normal','hypertension','hypotension','temp_normal','hypothermia'].includes(prefix)) groups.vit++;
    else if (prefix === 'hx') groups.hx++;
    else if (prefix === 'risk') groups.risk++;
    else if (prefix === 'med') groups.med++;
    else groups.ctx++;
  });
  
  const max = Math.max(...Object.values(groups), 1);
  const bars = document.getElementById('holoBars');
  bars.innerHTML = '';
  const labels = { sym: 'Symptomes', vit: 'Vitaux', hx: 'Historique', risk: 'Risques', med: 'Medics', ctx: 'Contexte' };
  const colors = { sym: '#d4a853', vit: '#27ae60', hx: '#3498db', risk: '#e74c3c', med: '#8e44ad', ctx: '#e67e22' };
  
  let legendHTML = '';
  for (const [key, count] of Object.entries(groups)) {
    if (count > 0) {
      const pct = Math.round(count / max * 100);
      bars.innerHTML += '<div style="display:flex;align-items:center;gap:8px;font-size:10px;margin:3px 0"><span style="min-width:55px;color:#8b7355">' + labels[key] + '</span><div class="holo-bar" style="flex:1"><div class="holo-bar-fill ' + key + '" style="width:' + pct + '%"></div></div><span style="color:' + colors[key] + '">' + count + '</span></div>';
    }
  }
  
  const explanation = Hologram.explain(holo);
  aiAddMessage('🧬 **Hologramme du patient**\n' + explanation + '\n\n' + holo.features.length + ' caracteristiques harmoniques encodees dans C⁵¹².', 'ai');
}

async function aiQuickTeach() {
  await ensureAI();
  const diag = getLastDiagnosis();
  if (!diag) {
    aiAddMessage('Lancez un diagnostic d\'abord pour acceder au mode formation.', 'system');
    return;
  }
  const holo = buildCurrentHologram();
  const lesson = kaAI.teach(diag.top, holo);
  aiAddMessage(lesson, 'ai');
}

async function aiQuickSearch() {
  await ensureAI();
  const q = prompt('Recherche medicale (medicament, protocole, posologie...) :');
  if (!q) return;
  aiAddMessage('🔍 ' + q, 'user');
  kaAI.searchMedical(q).then(answer => {
    aiAddMessage(answer, 'ai');
  });
}

async function aiQuickDrug() {
  await ensureAI();
  const q = prompt('Nom du medicament :');
  if (!q) return;
  aiAddMessage('💊 ' + q, 'user');
  kaAI.searchMedical('médicament ' + q).then(answer => {
    aiAddMessage(answer, 'ai');
  });
}

async function aiQuickMereEnfant() {
  await ensureAI();
  aiAddMessage('🤰 Protocoles Mère-Enfant disponibles :', 'user');
  const protos = ['pre_eclampsie','eclampsie','hemorragie_post_partum','infection_neonatale','asphyxie_neonatale','prematurite','ictere_neonatal','allaitement_difficile','contraception_post_partum','cpn1'];
  const list = protos.map(p => '• ' + p.replace(/_/g, ' ')).join('\n');
  aiAddMessage('🏥 Protocoles disponibles :\n' + list + '\n\nTapez le nom du protocole pour la fiche complete.', 'ai');
}

// Bouton "❓ Affiner" — pose une question discriminante sur les différentiels
async function aiQuickClarify() {
  await ensureAI();
  const diag = getLastDiagnosis();
  if (!diag || !diag.scores || diag.scores.length < 2) {
    aiAddMessage('Lancez un diagnostic d\'abord pour affiner.', 'system');
    return;
  }
  const q = kaAI.askClarifyingQuestion(diag.scores, askedQuestions);
  if (!q) {
    aiAddMessage('✅ Le diagnostic est suffisamment tranche (ecart > 25 pts) ou toutes les questions ont ete posees.', 'ai');
    return;
  }
  askedQuestions.push(q);
  pendingClarification = true;
  aiAddMessage('❓ **Question de clarification**\n' + q + '\n\n_Repondez directement dans le chat (oui/non ou decrivez)._', 'ai');
}

// Propose automatiquement une question après une explication (boucle de clarification)
function aiSuggestClarification(diag) {
  if (!kaAI || !diag || !diag.scores || diag.scores.length < 2) return;
  const q = kaAI.askClarifyingQuestion(diag.scores, askedQuestions);
  if (!q) return;
  askedQuestions.push(q);
  pendingClarification = true;
  aiAddMessage('❓ **Pour affiner :** ' + q, 'ai');
}

function getLastDiagnosis() {
  // 1) Données complètes en mémoire (diagnostic de cette session) — conduite, délai, différentiels
  if (lastDiagnosisData) return lastDiagnosisData;

  // 2) Reconstruction depuis l'historique enrichi
  if (!diagnosticHistory || diagnosticHistory.length === 0) return null;
  const last = diagnosticHistory[0];
  const top = {
    name: last.diagnosis,
    score: parseFloat(last.score) / 100,
    g: last.gravity || (last.urgent ? 'URGENCE' : 'MODEREE'),
    u: !!last.urgent,
    c: last.advice || '',
    d: last.delay || ''
  };
  return { top, scores: [top], symptoms: last.symptoms || '', date: last.date, patientId: null };
}

function buildCurrentHologram() {
  const symptoms = document.getElementById('symptomsInput')?.value || '';
  const age = document.getElementById('patientAge')?.value || '';
  const gender = document.getElementById('patientGender')?.value || '';
  
  // Donnees enrichies depuis le patient selectionne
  let history = [], medications = [], allergies = [], riskFactors = [];
  if (currentPatient) {
    history = currentPatient.history || [];
    medications = currentPatient.medications || [];
    allergies = currentPatient.allergies || [];
    riskFactors = currentPatient.riskFactors || currentPatient.risks || [];
    if (currentPatient.age && !age) document.getElementById('patientAge').value = currentPatient.age;
    if (currentPatient.gender && !gender) document.getElementById('patientGender').value = currentPatient.gender;
  }
  
  return Hologram.encode({
    symptoms,
    demographics: { age: age || (currentPatient?.age || ''), gender: gender || (currentPatient?.gender || '') },
    history,
    medications,
    allergies,
    riskFactors,
    context: { season: 'rainy', region: 'tropical' }
  });
}

// ── Initialisation bouton retour physique Android ──
// Appelé dès que le DOM est prêt (l'app démarre sur splash sans init explicite).
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', setupAndroidBackButton);
} else {
  setupAndroidBackButton();
}
