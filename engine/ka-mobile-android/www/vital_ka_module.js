/* ══════════════════════════════════════════════════════════════════════════
   VITAL KA MODULE — L'univers santé-social dans KA Mobile
   ══════════════════════════════════════════════════════════════════════════
   KA Mobile = plateforme IA mondiale (univers KA).
   Ce module = univers VITAL KA (Fondation) : santé + paiement social.

   Contenu :
     • Wallet UM (solde, recevoir, payer prestataire)
     • Dossier médical (sync serveur /records)
     • Téléconsultation par lien (diaspora)
     • Ordonnances QR

   Identité unifiée : ka_user_id (KA Mobile) → walletId Vital Ka.
   Serveur Vital Ka : configurable (ka_api_url) — fallback local.
   ══════════════════════════════════════════════════════════════════════════ */
(function (global) {
  'use strict';

  // ── Config ──
  var VK_API = (function () {
    try { var u = localStorage.getItem('ka_vitalka_url'); if (u) return u; } catch (e) {}
    return 'http://localhost:8000';
  })();
  var STORE = 'ka_vitalka_data';

  // ── Identité unifiée ──
  function getUserId() {
    var uid = null;
    try { uid = localStorage.getItem('ka_user_id'); } catch (e) {}
    if (!uid) {
      uid = 'user_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
      try { localStorage.setItem('ka_user_id', uid); } catch (e) {}
    }
    return uid;
  }

  function loadData() {
    try { return JSON.parse(localStorage.getItem(STORE) || '{}'); } catch (e) { return {}; }
  }
  function saveData(d) { localStorage.setItem(STORE, JSON.stringify(d)); }

  // ── Activation intelligente ──
  var ACTIVATION_KEY = 'ka_vitalka_activated';
  function isActivated() {
    try {
      var v = localStorage.getItem(ACTIVATION_KEY);
      if (v === 'true') return true;
      if (v === 'false') return false;
    } catch (e) {}
    // Auto-détection pays (simple) : langue/indices — à affiner avec géoloc
    var lang = (navigator.language || '').toLowerCase();
    if (lang === 'fr' || lang === 'fr-fr') return false; // France = diaspora, pas auto
    return false; // défaut : pas activé, l'utilisateur choisit
  }
  function activate() { localStorage.setItem(ACTIVATION_KEY, 'true'); }
  function deactivate() { localStorage.setItem(ACTIVATION_KEY, 'false'); }

  // ── API wallet ──
  function getWalletId() {
    // walletId déterministe depuis ka_user_id (stable sur tous les appareils)
    return 'KA' + getUserId().replace(/[^a-zA-Z0-9]/g, '').slice(0, 12).toUpperCase();
  }

  // Crée le compte patient côté serveur (idempotent : 409 si déjà existant)
  async function ensureAccount() {
    var wid = getWalletId();
    try {
      var res = await fetch(VK_API + '/api/v1/wallet/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          owner_id: wid,
          role: 'patient',
          public_id: wid
        })
      });
      if (res.ok || res.status === 409) return { ok: true, exists: res.status === 409 };
      return { ok: false, error: 'create refusé (' + res.status + ')' };
    } catch (e) {
      return { ok: false, error: 'serveur injoignable' };
    }
  }

  async function fetchBalance() {
    var wid = getWalletId();
    try {
      var res = await fetch(VK_API + '/api/v1/wallet/' + encodeURIComponent(wid) + '/balance');
      if (res.ok) {
        var d = await res.json();
        return { ok: true, balance_um: d.balance_um, balance_cfa: d.balance_cfa, public_id: d.public_id };
      }
      if (res.status === 404) {
        // Compte pas encore créé → solde 0 (le premier crédit créera)
        return { ok: true, balance_um: 0, balance_cfa: 0, public_id: wid, no_account: true };
      }
    } catch (e) {}
    // Fallback local
    var data = loadData();
    return { ok: true, balance_um: data.balance_um || 0, balance_cfa: (data.balance_um || 0) * 655, public_id: wid, local: true };
  }

  async function creditFromSolidarity(amountUm, currency) {
    var wid = getWalletId();
    // Garantir le compte serveur avant le crédit
    var acc = await ensureAccount();
    try {
      var res = await fetch(VK_API + '/api/v1/wallet/credit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          owner_id: wid,
          amount_um: amountUm,
          type: 'solidarite_credit',
          reference: 'KA-SOL-' + Date.now(),
          metadata: { currency: currency || 'CFA' }
        })
      });
      if (res.ok) {
        var d = await res.json();
        return { ok: true, tx_id: d.tx_id, balance_after: d.balance_after, server: true };
      }
      var err = await res.json();
      return { ok: false, error: err.detail || ('Refusé (' + res.status + ')') };
    } catch (e) {}
    // Fallback local
    var data = loadData();
    data.balance_um = (data.balance_um || 0) + amountUm;
    saveData(data);
    return { ok: true, balance_after: data.balance_um, server: false };
  }

  async function payProvider(providerWalletId, amountUm, reference) {
    var wid = getWalletId();
    try {
      var res = await fetch(VK_API + '/api/v1/wallet/pay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from_owner_id: wid,
          to_owner_id: providerWalletId,
          amount_um: amountUm,
          reference: reference || ('KA-PAY-' + Date.now())
        })
      });
      if (res.ok) {
        var d = await res.json();
        return { ok: true, tx_id: d.tx_id, from_balance: d.from_balance_after, server: true };
      }
      var err = await res.json();
      return { ok: false, error: err.detail || 'Refusé' };
    } catch (e) {
      return { ok: false, error: 'Serveur injoignable' };
    }
  }

  // ── Dossier médical ──
  async function syncRecord() {
    var wid = getWalletId();
    try {
      var res = await fetch(VK_API + '/api/v1/records/' + encodeURIComponent(wid));
      if (res.ok) {
        var d = await res.json();
        return { ok: true, record: d };
      }
      if (res.status === 404) return { ok: false, not_found: true };
    } catch (e) {}
    return { ok: false, error: 'serveur injoignable' };
  }

  // ── Téléconsultation lien ──
  async function createTeleconsultLink(patientName, amountUm) {
    var wid = getWalletId();
    try {
      var res = await fetch(VK_API + '/api/v1/teleconsult/link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: wid,
          patient_name: patientName || 'Patient KA',
          amount_um: amountUm || 0
        })
      });
      if (res.ok) {
        var d = await res.json();
        return { ok: true, link: d.link, token: d.token };
      }
    } catch (e) {}
    return { ok: false, error: 'serveur injoignable' };
  }

  // ── Rendu (injecté dans l'écran #s-vitalka) ──
  function render() {
    var root = document.getElementById('vitalka-module');
    if (!root) return;
    var data = loadData();
    var activated = isActivated();
    var userName = '';
    try { userName = JSON.parse(localStorage.getItem('ka_user') || '{}').name || ''; } catch (e) {}

    if (!activated) {
      root.innerHTML =
        '<div style="text-align:center;padding:24px 16px">'
        + '<div style="font-size:44px;margin-bottom:8px">🌍</div>'
        + '<h3 style="color:var(--t1);margin-bottom:8px">Vital Ka — La santé pour tous</h3>'
        + '<p style="color:var(--t4);font-size:12px;line-height:1.6;margin-bottom:16px">Un univers de santé porté par la Fondation KA : portefeuille de soins (UM), dossier médical, téléconsultation avec un médecin où qu\'il soit.</p>'
        + '<div class="btn btn--life" style="width:auto;margin:0 auto" onclick="VitalKaModule.activate()">✨ Activer Vital Ka</div>'
        + '<p style="color:var(--t4);font-size:10px;margin-top:10px">Gratuit — financé par la solidarité et la Fondation KA</p>'
        + '</div>';
      return;
    }

    // Écran actif : wallet + santé
    root.innerHTML =
      '<div style="padding:12px">'
      // Solde
      + '<div style="background:rgba(139,131,255,.08);border:.5px solid rgba(139,131,255,.25);border-radius:16px;padding:16px;text-align:center;margin-bottom:10px">'
      + '<div style="font-size:10px;color:var(--t4);text-transform:uppercase">Portefeuille santé</div>'
      + '<div style="font-size:32px;font-weight:800;color:var(--t1)" id="vk-balance">—</div>'
      + '<div style="font-size:11px;color:var(--t4)" id="vk-balance-cfa"></div>'
      + '<div style="font-size:9px;color:var(--t4)" id="vk-wallet-id"></div>'
      + '</div>'
      // Actions
      + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px">'
      + '<div class="card" style="cursor:pointer;text-align:center;padding:14px" onclick="VitalKaModule.showCredit()"><div style="font-size:22px">💝</div><div style="font-size:11px;color:var(--t2)">Recevoir (solidarité)</div></div>'
      + '<div class="card" style="cursor:pointer;text-align:center;padding:14px" onclick="VitalKaModule.showPay()"><div style="font-size:22px">🏪</div><div style="font-size:11px;color:var(--t2)">Payer un soin</div></div>'
      + '<div class="card" style="cursor:pointer;text-align:center;padding:14px" onclick="VitalKaModule.showRecord()"><div style="font-size:22px">📁</div><div style="font-size:11px;color:var(--t2)">Dossier médical</div></div>'
      + '<div class="card" style="cursor:pointer;text-align:center;padding:14px" onclick="VitalKaModule.showTeleconsult()"><div style="font-size:22px">🔗</div><div style="font-size:11px;color:var(--t2)">Consulter un médecin</div></div>'
      + '</div>'
      // Zone résultat
      + '<div id="vk-result" style="font-size:12px;color:var(--t2)"></div>'
      // Désactivation
      + '<div style="text-align:center;margin-top:12px"><span style="font-size:10px;color:var(--t4);cursor:pointer" onclick="VitalKaModule.deactivate()">Désactiver Vital Ka</span></div>'
      + '</div>';

    // Charger le solde
    fetchBalance().then(function (b) {
      var el = document.getElementById('vk-balance');
      if (el) el.textContent = b.balance_um + ' UM';
      var cfa = document.getElementById('vk-balance-cfa');
      if (cfa) cfa.textContent = '= ' + b.balance_cfa.toLocaleString('fr-FR') + ' FCFA';
      var wid = document.getElementById('vk-wallet-id');
      if (wid) wid.textContent = 'ID: ' + b.public_id + (b.local ? ' (local)' : '');
    });
  }

  // ── UI actions ──
  function showCredit() {
    var el = document.getElementById('vk-result');
    var amount = parseInt(prompt('Montant reçu (UM) :'), 10);
    if (!amount || amount < 1) return;
    el.innerHTML = '<span style="color:var(--t4)">Enregistrement...</span>';
    creditFromSolidarity(amount, 'CFA').then(function (r) {
      el.innerHTML = r.ok
        ? '<span style="color:var(--life)">✅ ' + amount + ' UM reçues (solde ' + r.balance_after + ')' + (r.server ? ' — tracé serveur' : ' — local') + '</span>'
        : '<span style="color:var(--coral)">❌ ' + r.error + '</span>';
      render();
    });
  }

  function showPay() {
    var el = document.getElementById('vk-result');
    var provider = prompt('ID du prestataire (pharmacie/médecin) :');
    if (!provider) return;
    var amount = parseInt(prompt('Montant (UM) :'), 10);
    if (!amount || amount < 1) return;
    el.innerHTML = '<span style="color:var(--t4)">Paiement...</span>';
    payProvider(provider, amount).then(function (r) {
      el.innerHTML = r.ok
        ? '<span style="color:var(--life)">✅ Paiement de ' + amount + ' UM — tx ' + r.tx_id + '</span>'
        : '<span style="color:var(--coral)">❌ ' + r.error + '</span>';
      render();
    });
  }

  function showRecord() {
    var el = document.getElementById('vk-result');
    el.innerHTML = '<span style="color:var(--t4)">Chargement du dossier...</span>';
    syncRecord().then(function (r) {
      if (r.ok) {
        var rec = r.record;
        var p = rec.profile || {};
        el.innerHTML =
          '<div style="background:rgba(15,15,25,.6);border:.5px solid var(--b2);border-radius:12px;padding:12px">'
          + '<div style="font-weight:600;margin-bottom:6px">👤 ' + (p.name || 'Patient KA') + '</div>'
          + '<div style="font-size:11px;color:var(--t2)">⚠️ Allergies : ' + ((rec.allergies || []).join(', ') || 'aucune') + '</div>'
          + '<div style="font-size:11px;color:var(--t2)">📋 Antécédents : ' + ((rec.antecedents || []).join(', ') || '—') + '</div>'
          + '<div style="font-size:11px;color:var(--t2)">💊 Médicaments : ' + ((rec.medications || []).map(function (m) { return m.name || m.medication || ''; }).join(', ') || '—') + '</div>'
          + '<div style="font-size:9px;color:var(--t4);margin-top:6px">Sync serveur : ' + new Date(rec.updated_at).toLocaleString('fr-FR') + '</div>'
          + '</div>';
      } else if (r.not_found) {
        el.innerHTML = '<span style="color:var(--wisdom)">📁 Aucun dossier sur le serveur. Créez-le depuis l\'app Vital Ka (médecin/patient).</span>';
      } else {
        el.innerHTML = '<span style="color:var(--coral)">❌ ' + (r.error || 'Serveur injoignable') + '</span>';
      }
    });
  }

  function showTeleconsult() {
    var el = document.getElementById('vk-result');
    var amount = parseInt(prompt('Honoraires convenus (UM) — 0 si à convenir :') || '0', 10) || 0;
    var name = '';
    try { name = JSON.parse(localStorage.getItem('ka_user') || '{}').name || ''; } catch (e) {}
    el.innerHTML = '<span style="color:var(--t4)">Génération du lien...</span>';
    createTeleconsultLink(name, amount).then(function (r) {
      if (!r.ok) {
        el.innerHTML = '<span style="color:var(--coral)">❌ ' + r.error + '</span>';
        return;
      }
      el.innerHTML =
        '<div style="background:rgba(139,131,255,.08);border:.5px solid rgba(139,131,255,.25);border-radius:12px;padding:12px;text-align:center">'
        + '<div style="font-size:11px;color:var(--t4);margin-bottom:4px">🔗 Lien de consultation (30 min)</div>'
        + '<div style="font-size:11px;word-break:break-all;color:var(--soul-l);margin-bottom:8px">' + r.link + '</div>'
        + '<div style="display:flex;gap:6px;justify-content:center">'
        + '<button onclick="VitalKaModule.shareLink(\'' + r.link + '\',\'whatsapp\')" style="background:#25D366;color:#fff;border:none;border-radius:8px;padding:8px 14px;cursor:pointer;font-size:11px">WhatsApp</button>'
        + '<button onclick="VitalKaModule.shareLink(\'' + r.link + '\',\'copy\')" style="background:rgba(255,255,255,.1);color:var(--t1);border:.5px solid var(--b2);border-radius:8px;padding:8px 14px;cursor:pointer;font-size:11px">Copier</button>'
        + '</div></div>';
    });
  }

  function shareLink(link, mode) {
    var msg = '🔗 Consultation Vital Ka — cliquez pour démarrer : ' + link;
    if (mode === 'whatsapp') {
      window.open('https://wa.me/?text=' + encodeURIComponent(msg), '_blank');
    } else {
      navigator.clipboard.writeText(link).then(function () { alert('✅ Lien copié !'); });
    }
  }

  // ── API publique ──
  global.VitalKaModule = {
    render: render,
    activate: function () { activate(); render(); },
    deactivate: function () { deactivate(); render(); },
    isActivated: isActivated,
    showCredit: showCredit,
    showPay: showPay,
    showRecord: showRecord,
    showTeleconsult: showTeleconsult,
    shareLink: shareLink,
    getWalletId: getWalletId
  };

  if (global.console && console.log) console.log('Vital Ka · module santé-social chargé');

})(typeof window !== 'undefined' ? window : this);
