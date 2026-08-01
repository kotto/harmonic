/**
 * KA Platform — Core unifié de l'écosystème Vital Ka
 * ====================================================
 * Gère la session utilisateur cross-app, la synchronisation wallet,
 * le bus de notifications inter-apps, et le routage.
 * 
 * Stockage :
 *   ka_platform_session   → session utilisateur courante
 *   ka_platform_profile   → profil plateforme (nom, rôle, avatar)
 *   ka_platform_events    → bus d'événements inter-apps
 *   ka_platform_config    → configuration globale
 */

'use strict';

const KA_PLATFORM = (() => {
  const VERSION = '1.0.0';
  const STORE_SESSION = 'ka_platform_session';
  const STORE_PROFILE = 'ka_platform_profile';
  const STORE_EVENTS = 'ka_platform_events';
  const STORE_CONFIG = 'ka_platform_config';

  // ── Rôles ──
  const ROLES = {
    PATIENT: 'patient',
    MEDECIN: 'medecin',
    PHARMACIEN: 'pharmacien',
    SOLIDARITE: 'solidarite',
    ADMIN: 'admin',
  };

  // ── Session ──
  function getSession() {
    try { return JSON.parse(localStorage.getItem(STORE_SESSION)); } catch(e) { return null; }
  }
  function setSession(s) { localStorage.setItem(STORE_SESSION, JSON.stringify(s)); }
  function clearSession() { localStorage.removeItem(STORE_SESSION); }

  function login(role, name, userId) {
    const session = {
      id: userId || 'user_' + Date.now().toString(36),
      role: role,
      name: name || ('Utilisateur ' + role),
      loginAt: new Date().toISOString(),
      appVersion: VERSION,
    };
    setSession(session);
    // Initialiser le wallet du rôle si pas encore créé
    if (typeof KA_WALLET !== 'undefined') {
      const wallet = KA_WALLET.getWallet(role);
      if (!wallet.walletId) {
        KA_WALLET.getWallet(role); // force init
      }
    }
    // Émettre événement login
    emit('login', { role, name, userId: session.id });
    return session;
  }

  function logout() {
    const session = getSession();
    if (session) emit('logout', { role: session.role });
    clearSession();
  }

  function getCurrentUser() { return getSession(); }
  function getCurrentRole() { return (getSession() || {}).role; }

  // ── Profil plateforme ──
  function getProfile() {
    try { return JSON.parse(localStorage.getItem(STORE_PROFILE)); } catch(e) { return {}; }
  }
  function updateProfile(patch) {
    const profile = getProfile();
    Object.assign(profile, patch);
    profile.updatedAt = new Date().toISOString();
    localStorage.setItem(STORE_PROFILE, JSON.stringify(profile));
    emit('profile_updated', profile);
    return profile;
  }

  // ── Bus d'événements inter-apps ──
  function emit(event, data) {
    const events = getEvents();
    events.push({ event, data, timestamp: new Date().toISOString() });
    if (events.length > 200) events.splice(0, events.length - 200);
    localStorage.setItem(STORE_EVENTS, JSON.stringify(events));
    // BroadcastChannel pour onglets ouverts
    try {
      const bc = new BroadcastChannel('ka_platform');
      bc.postMessage({ event, data, timestamp: Date.now() });
      bc.close();
    } catch(e) {}
  }

  function getEvents() {
    try { return JSON.parse(localStorage.getItem(STORE_EVENTS) || '[]'); } catch(e) { return []; }
  }

  function getRecentEvents(since) {
    const events = getEvents();
    if (!since) return events.slice(-20);
    return events.filter(e => e.timestamp >= since);
  }

  /**
   * Écoute les événements inter-apps via BroadcastChannel.
   */
  function onEvent(callback) {
    try {
      const bc = new BroadcastChannel('ka_platform');
      bc.onmessage = (msg) => { if (callback) callback(msg.data); };
      return bc;
    } catch(e) { return null; }
  }

  // ── Wallet sync cross-app ──
  function syncWallet() {
    const session = getSession();
    if (!session) return null;
    if (typeof KA_WALLET === 'undefined') return null;
    const wallet = KA_WALLET.getWallet(session.role);
    const profile = getProfile();
    // Mettre à jour le profil avec le walletId
    if (wallet.walletId && profile.walletId !== wallet.walletId) {
      updateProfile({ walletId: wallet.walletId });
    }
    return wallet;
  }

  /**
   * Vérifie si des crédits solidarité sont arrivés depuis la dernière vérification.
   */
  function checkPendingCredits() {
    const session = getSession();
    if (!session) return [];
    if (typeof KA_WALLET === 'undefined') return [];
    const wallet = KA_WALLET.getWallet(session.role);
    const lastCheck = getProfile().lastCreditCheck || session.loginAt;
    const newCredits = wallet.transactions.filter(tx => 
      tx.direction === 'in' && tx.timestamp > lastCheck
    );
    updateProfile({ lastCreditCheck: new Date().toISOString() });
    return newCredits;
  }

  // ── Routage → app ──
  function routeToApp() {
    const session = getSession();
    if (!session) return 'ka_launcher.html';
    const role = session.role;
    const routeMap = {
      [ROLES.MEDECIN]: 'vital_ka.html',
      [ROLES.PATIENT]: 'ka_patient.html',
      [ROLES.PHARMACIEN]: 'ka_pharmacien.html',
      [ROLES.SOLIDARITE]: 'ka_solidarite.html',
      [ROLES.ADMIN]: 'ka_admin.html',
    };
    return routeMap[role] || 'ka_launcher.html';
  }

  function openApp(role) {
    const routeMap = {
      [ROLES.MEDECIN]: 'vital_ka.html',
      [ROLES.PATIENT]: 'ka_patient.html',
      [ROLES.PHARMACIEN]: 'ka_pharmacien.html',
      [ROLES.SOLIDARITE]: 'ka_solidarite.html',
      [ROLES.ADMIN]: 'ka_admin.html',
    };
    const url = routeMap[role] || 'ka_launcher.html';
    window.open(url, '_blank');
  }

  // ── Configuration globale ──
  function getConfig() {
    try { return JSON.parse(localStorage.getItem(STORE_CONFIG)) || {}; } catch(e) { return {}; }
  }
  function setConfig(key, value) {
    const cfg = getConfig();
    cfg[key] = value;
    localStorage.setItem(STORE_CONFIG, JSON.stringify(cfg));
  }

  // ── Stats agrégées (pour dashboard admin) ──
  function getAggregateStats() {
    const ledger = typeof KA_WALLET !== 'undefined' ? KA_WALLET.getLedger() : [];
    const now = new Date();
    const today = now.toISOString().slice(0, 10);
    
    let totalTx = ledger.length;
    let todayTx = ledger.filter(tx => tx.timestamp.slice(0, 10) === today).length;
    let totalVolume = ledger.reduce((s, tx) => s + tx.amount, 0);
    let todayVolume = ledger.filter(tx => tx.timestamp.slice(0, 10) === today)
      .reduce((s, tx) => s + tx.amount, 0);

    // Compter les wallets
    let patients = 0, pharmacies = 0, medecins = 0;
    for (const tx of ledger) {
      if (tx.to && tx.to.startsWith('PATIE')) patients++;
      if (tx.to && tx.to.startsWith('PHARM')) pharmacies++;
      if (tx.to && tx.to.startsWith('MEDEC')) medecins++;
    }

    return { totalTx, todayTx, totalVolume, todayVolume, patients, pharmacies, medecins, version: VERSION };
  }

  // ═══ API PUBLIQUE ═══
  return {
    VERSION, ROLES,
    login, logout, getSession, getCurrentUser, getCurrentRole,
    getProfile, updateProfile,
    emit, getEvents, getRecentEvents, onEvent,
    syncWallet, checkPendingCredits,
    routeToApp, openApp,
    getConfig, setConfig,
    getAggregateStats,
  };
})();

if (typeof window !== 'undefined') window.KA_PLATFORM = KA_PLATFORM;
