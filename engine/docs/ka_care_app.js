/**
 * KA Care App — Logique métier (extracted from ka_care.html)
 * =============================================================
 * Gère : patients, diagnostic, historique, vitals, navigation
 * Dépendances : ka_core.js (DB, encodeSympt, cosineSim, F)
 *               ka_secure.js, ka_bridge.js, ka_care_ble.js
 */

const PK = 'ka_care_patients';
let currentPatient = null;
let diagnosticHistory = JSON.parse(localStorage.getItem('ka_care_history') || '[]');
let currentScreen = 'splash';

// ═══ PATIENTS ═══
function loadPatients() { try { return JSON.parse(localStorage.getItem(PK) || '{}'); } catch (e) { return {}; } }
function savePatients(pts) { localStorage.setItem(PK, JSON.stringify(pts)); }
function refreshPatientSelect() {
  const pts = loadPatients();
  const sel = document.getElementById('patientSelect');
  if (!sel) return;
  sel.innerHTML = '<option value="">👤 Patient anonyme</option>';
  for (const [id, p] of Object.entries(pts)) {
    sel.innerHTML += '<option value="' + id + '">' + p.name + ' (' + (p.history ? p.history.length : 0) + ' diags)</option>';
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
    idEl.textContent = 'ID: ' + currentPatient.id;
  }
}

// ═══ SCREENS ═══
function showScreen(name) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const el = document.getElementById('screen-' + name);
  if (el) el.classList.add('active');
  currentScreen = name;
  document.getElementById('bottomNav').style.display = (name === 'splash') ? 'none' : 'flex';
  document.querySelectorAll('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.screen === name));
  if (name === 'history') renderHistory();
  if (name === 'vitals') renderVitals();
  if (name === 'patients') renderPatients();
  if (name === 'resonance') refreshPatientSelect();
  if (name === 'dossier') updateDossier();
}

// ═══ DIAGNOSTIC ═══
function diagnose() {
  const text = document.getElementById('symptomsInput').value.trim();
  if (!text) return;
  const btn = document.getElementById('diagnoseBtn');
  btn.disabled = true;
  btn.textContent = 'Analyse en cours...';
  document.getElementById('resultsArea').innerHTML = '<div class="spinner"></div>';

  setTimeout(() => {
    const pVec = encodeSympt(text);
    if (currentPatient && currentPatient.history) {
      for (const past of currentPatient.history.slice(-5)) {
        const pv = encodeSympt(past);
        for (const f of F) if ((pv[f] || 0) > 0) pVec[f] = (pVec[f] || 0) + 0.15;
      }
    }

    const scores = [];
    for (const [n, d] of Object.entries(DB)) {
      scores.push({ name: n, score: cosineSim(pVec, encodeSympt(d.s.join(' '))), ...d });
    }
    scores.sort((a, b) => b.score - a.score);
    const top = scores[0];

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

    if (currentPatient && top && top.score > 0.4) {
      const pts = loadPatients();
      if (pts[currentPatient.id]) {
        if (!pts[currentPatient.id].history) pts[currentPatient.id].history = [];
        pts[currentPatient.id].history.push(top.name + ' (' + (top.score * 100).toFixed(0) + '%)');
        if (pts[currentPatient.id].history.length > 20) pts[currentPatient.id].history = pts[currentPatient.id].history.slice(-20);
        savePatients(pts);
        currentPatient = { id: currentPatient.id, ...pts[currentPatient.id] };
      }
      diagnosticHistory.unshift({ date: new Date().toISOString(), symptoms: text, diagnosis: top.name, score: (top.score * 100).toFixed(0), urgent: top.u });
      if (diagnosticHistory.length > 50) diagnosticHistory = diagnosticHistory.slice(0, 50);
      localStorage.setItem('ka_care_history', JSON.stringify(diagnosticHistory));
    }

    h += '<p class="footer-note">AIDE AU DIAGNOSTIC — NE REMPLACE PAS UN MÉDECIN</p>';
    document.getElementById('resultsArea').innerHTML = h;
    btn.disabled = false;
    btn.textContent = '🔍 Nouveau diagnostic';

    const eb = document.getElementById('exportDiagBtn');
    if (eb && currentPatient) eb.style.display = 'block';

    // ── Complément holographique (base de connaissances HWAT) ──
    // L'API est interrogée en parallèle ; si elle est absente,
    // KA_AI.query renvoie [] et rien n'est affiché (mode local pur).
    if (typeof KA_AI !== 'undefined') {
      KA_AI.query(text, 4).then(facts => {
        if (!facts.length) return;
        const area = document.getElementById('resultsArea');
        if (area) area.innerHTML += KA_AI.renderFacts(facts);
      });
    }
  }, 150);
}

// ═══ HISTORY ═══
function renderHistory() {
  const el = document.getElementById('historyList');
  if (!el) return;
  if (!diagnosticHistory.length) { el.innerHTML = '<div class="card"><p style="text-align:center;color:var(--muted)">Aucun diagnostic.</p></div>'; return; }
  let h = '';
  for (const d of diagnosticHistory.slice(0, 20)) {
    const dt = new Date(d.date);
    h += '<div class="history-item' + (d.urgent ? ' urgent' : '') + '"><div class="date">' + dt.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) + '</div><strong>' + d.diagnosis + '</strong> <span style="color:var(--accent);font-weight:700">' + d.score + '%</span><div style="font-size:13px;color:var(--on-surface-variant);margin-top:4px">' + d.symptoms.substring(0, 80) + '</div></div>';
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
  let h = '<div style="margin-bottom:12px;display:flex;gap:8px"><input id="newPatientInput" placeholder="Nom du patient..." style="flex:1;background:#141414;color:#d4c8a0;border:1px solid #2a2a2a;padding:10px 14px;border-radius:10px;font-size:14px;font-family:inherit"><button class="btn btn-sm btn-primary" onclick="addPatient()">➕ Ajouter</button></div>';
  if (!keys.length) h += '<div class="card"><p style="text-align:center;color:var(--muted)">Aucun patient.</p></div>';
  for (let i = keys.length - 1; i >= Math.max(0, keys.length - 10); i--) {
    const id = keys[i], p = pts[id];
    h += '<div class="patient-row" onclick="currentPatient={id:\'' + id + '\',...loadPatients()[\'' + id + '\']};showScreen(\'resonance\');refreshPatientSelect()"><div class="avatar">' + (p.name || '?')[0].toUpperCase() + '</div><div class="info"><div class="name">' + p.name + '</div><div class="meta">' + (p.history ? p.history.length : 0) + ' diagnostics</div></div><span class="material-symbols-outlined">chevron_right</span></div>';
  }
  el.innerHTML = h;
}
function addPatient() {
  const n = (document.getElementById('newPatientInput')?.value || '').trim();
  if (!n) return;
  const pts = loadPatients();
  const id = 'p' + Date.now();
  pts[id] = { name: n, history: [], createdAt: new Date().toISOString() };
  savePatients(pts);
  document.getElementById('newPatientInput').value = '';
  renderPatients();
  refreshPatientSelect();
}

// ═══ BRIDGE ═══
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
  const results = document.getElementById('resultsArea');
  if (results) {
    const first = results.querySelector('.result-item strong');
    if (first) diag.diagnostic_principal.maladie = first.textContent.replace('🚨', '').trim();
  }
  if (!diag.diagnostic_principal.maladie) { alert('Lancez un diagnostic d\'abord.'); return; }
  const pkg = KA_BRIDGE.doctorToPatient(diag, { name: currentPatient.name, id: currentPatient.id });
  const modal = document.createElement('div');
  modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.9);z-index:200;display:flex;align-items:center;justify-content:center;padding:20px';
  modal.innerHTML = '<div style="background:#1a1a1a;border:1px solid #d4a853;border-radius:16px;padding:24px;max-width:400px;text-align:center"><h3>📤 Transfert au patient</h3><div id="qrTransfer" style="margin:12px 0"></div><p style="font-size:.7em;color:#9b8f7e">Le patient scanne ce code avec KA Patient</p><button onclick="this.parentElement.parentElement.remove()" style="background:#d4a853;color:#0d0d0d;border:none;padding:10px 24px;border-radius:8px;cursor:pointer;margin-top:12px;font-weight:700;font-family:inherit">Fermer</button></div>';
  document.body.appendChild(modal);
  modal.onclick = function (e) { if (e.target === modal) modal.remove(); };
  KA_BRIDGE.generateQRCode ? KA_BRIDGE.generateQRCode('qrTransfer', pkg) : null;
}

// ═══ SECURITY ═══
function setupPIN() {
  const pin = prompt('Créez un code PIN à 4 chiffres :');
  if (!pin || pin.length !== 4 || !/^\d{4}$/.test(pin)) { alert('PIN invalide (4 chiffres requis).'); return; }
  if (KA_SECURE.setPIN(pin)) { alert('✅ PIN configuré !'); }
  else { alert('Erreur.'); }
}

// ═══ INIT ═══
KA_SECURE.showLockScreen(function () {
  refreshPatientSelect();
  // Quick symptom chips
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
  // Demo buttons
  [['🦠 Fievre + toux + anosmie', 'fievre, toux seche, fatigue, anosmie'], ['❤️ Douleur thoracique + sueurs', 'douleur thoracique, essoufflement, sueurs froides, nausees'], ['🌡️ Fievre cyclique + frissons', 'fievre cyclique, frissons, sueurs, maux de tete'], ['🦟 Fievre + douleurs articulaires', 'fievre elevee, douleurs articulaires, eruption cutanee']].forEach(([n, t]) => {
    const b = document.createElement('button');
    b.textContent = n; b.className = 'chip';
    b.onclick = () => { document.getElementById('symptomsInput').value = t; diagnose(); };
    document.getElementById('demoBtns').appendChild(b);
  });
});
