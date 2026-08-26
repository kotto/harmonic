/**
 * KA Wallet — Système de paiement en Unités Médicales (UM)
 * =========================================================
 * Module partagé utilisé par toutes les apps (patient, pharmacien, médecin, solidarité).
 * 
 * Principes :
 *   1 UM = 1 EUR = 655 CFA (taux fixe, non spéculatif)
 *   Non-convertible pour les patients (dépenses médicales uniquement)
 *   Convertible pour les prestataires (sur demande)
 *   Toutes les transactions sont signées HMAC et enregistrées dans le ledger central
 * 
 * Stockage :
 *   ka_wallet_{role}    → solde + transactions par rôle
 *   ka_ledger           → registre central (append-only)
 *   ka_conversions       → demandes de conversion prestataire
 *
 * Depuis l'intégration Ecobank, le localStorage est un CACHE hors-ligne :
 * la source de vérité est le serveur /api/banking/* (KA_BANKING). Les
 * écritures critiques (conversion) sont poussées au serveur en best-effort.
 */
'use strict';

const KA_WALLET = (() => {
  // ── Constantes métier ──
  const UM_TO_EUR = 1;       // 1 UM = 1 EUR
  const UM_TO_CFA = 655;     // 1 UM = 655 CFA
  const QR_EXPIRY_MS = 5 * 60 * 1000; // 5 minutes
  const MAX_MONTHLY_SOLIDARITE = 5000; // limite anti-blanchiment

  // ── Rôles supportés ──
  const ROLES = ['patient', 'pharmacie', 'medecin', 'labo', 'solidarite'];

  // ═══ LEDGER CENTRAL ═══
  function getLedger() {
    try { return JSON.parse(localStorage.getItem('ka_ledger') || '[]'); }
    catch(e) { return []; }
  }
  function saveLedger(txs) {
    localStorage.setItem('ka_ledger', JSON.stringify(txs));
  }

  /**
   * Ajoute une transaction signée au ledger central.
   * @returns {object} la transaction créée
   */
  function recordTransaction(type, from, to, amount, metadata) {
    const tx = {
      txId: 'tx_' + Date.now() + '_' + Math.random().toString(36).slice(2, 6),
      type: type,        // 'solidarite_credit' | 'payment' | 'conversion'
      from: from,        // walletId de l'émetteur
      to: to,            // walletId du destinataire
      amount: Math.abs(amount),
      timestamp: new Date().toISOString(),
      metadata: metadata || {},
      sig: null,         // HMAC signé via KA_BRIDGE si dispo
    };
    // Signer si KA_BRIDGE est chargé
    if (typeof KA_BRIDGE !== 'undefined' && KA_BRIDGE.generateTransferCode) {
      try {
        const payload = { txId: tx.txId, type: tx.type, from: tx.from, to: tx.to, amount: tx.amount, ts: tx.timestamp };
        tx.sig = KA_BRIDGE.generateTransferCode(payload).slice(0, 64);
      } catch(e) {}
    }
    const ledger = getLedger();
    ledger.push(tx);
    if (ledger.length > 1000) ledger.splice(0, ledger.length - 1000);
    saveLedger(ledger);
    return tx;
  }

  // ═══ WALLET PER ROLE ═══
  function getWalletKey(role) {
    return 'ka_wallet_' + role;
  }

  function getWallet(role) {
    const key = getWalletKey(role);
    try {
      let w = JSON.parse(localStorage.getItem(key));
      if (!w || typeof w !== 'object') w = {};
      if (!Array.isArray(w.transactions)) w.transactions = [];
      if (typeof w.balance !== 'number') w.balance = 0;
      if (!w.walletId) w.walletId = role.toUpperCase().slice(0,5) + '-' + Math.random().toString(36).slice(2,8).toUpperCase();
      return w;
    } catch(e) {
      return { balance: 0, transactions: [], walletId: role.toUpperCase().slice(0,5) + '-' + Date.now().toString(36).toUpperCase() };
    }
  }

  function saveWallet(role, wallet) {
    localStorage.setItem(getWalletKey(role), JSON.stringify(wallet));
  }

  /**
   * Crédite un wallet (ex: solidarité → patient).
   */
  function credit(role, amount, description, metadata) {
    const wallet = getWallet(role);
    wallet.balance += Math.abs(amount);
    const tx = recordTransaction('solidarite_credit', 'KA_SOLIDARITE', wallet.walletId, amount, { description, ...metadata });
    wallet.transactions.push({ ...tx, direction: 'in' });
    saveWallet(role, wallet);
    return { wallet, tx };
  }

  /**
   * Débite un wallet (ex: patient → pharmacie).
   * Vérifie le solde avant débit.
   * @returns {{ ok: boolean, wallet: object, tx: object, error: string }}
   */
  function debit(role, amount, recipientRole, description, metadata) {
    const wallet = getWallet(role);
    if (wallet.balance < Math.abs(amount)) {
      return { ok: false, wallet, tx: null, error: 'Solde insuffisant. Disponible : ' + wallet.balance + ' UM' };
    }
    wallet.balance -= Math.abs(amount);
    const recipient = getWallet(recipientRole);
    const tx = recordTransaction('payment', wallet.walletId, recipient.walletId, amount, { description, ...metadata });
    wallet.transactions.push({ ...tx, direction: 'out' });
    saveWallet(role, wallet);
    // Créditer le destinataire
    recipient.balance += Math.abs(amount);
    recipient.transactions.push({ ...tx, direction: 'in' });
    saveWallet(recipientRole, recipient);
    return { ok: true, wallet, tx, recipient };
  }

  /**
   * Demande de conversion UM → monnaie locale (prestataire uniquement).
   */
  function requestConversion(role, amount, currency, bankInfo) {
    const wallet = getWallet(role);
    if (wallet.balance < amount) {
      return { ok: false, error: 'Solde insuffisant' };
    }
    const conv = {
      id: 'conv_' + Date.now(),
      role: role,
      walletId: wallet.walletId,
      amount: amount,
      currency: currency || 'CFA',
      convertedAmount: currency === 'EUR' ? Math.round(amount * UM_TO_EUR * 100) / 100 : Math.round(amount * UM_TO_CFA),
      bankInfo: bankInfo || {},
      status: 'pending',
      requestedAt: new Date().toISOString(),
      processedAt: null,
    };
    // Geler les fonds
    wallet.balance -= amount;
    wallet.pendingConversion = (wallet.pendingConversion || 0) + amount;
    saveWallet(role, wallet);
    // Enregistrer la demande
    const conversions = getConversions();
    conversions.push(conv);
    saveConversions(conversions);
    // Ledger
    recordTransaction('conversion_request', wallet.walletId, 'BANK', amount, { currency, bankInfo });

    // ── Sync serveur (best-effort, non-bloquant) ──
    // La source de vérité de l'argent est le SERVEUR bancaire (/api/banking/*).
    // Le localStorage reste un cache hors-ligne ; si KA_BANKING est chargé, on
    // pousse la demande et on mémorise l'identifiant serveur de la conversion.
    if (typeof KA_BANKING !== 'undefined' && KA_BANKING.requestConversion) {
      KA_BANKING.requestConversion(wallet.walletId, amount, currency, bankInfo)
        .then((res) => {
          if (res && res.ok && res.data && res.data.conversion) {
            conv.serverId = res.data.conversion.id;
            conv.serverStatus = res.data.conversion.status;
            const convs = getConversions();
            const i = convs.findIndex((c) => c.id === conv.id);
            if (i >= 0) { convs[i] = conv; saveConversions(convs); }
          }
        })
        .catch(() => {});
    }

    return { ok: true, conversion: conv, wallet };
  }

  function getConversions() {
    try { return JSON.parse(localStorage.getItem('ka_conversions') || '[]'); }
    catch(e) { return []; }
  }
  function saveConversions(convs) {
    localStorage.setItem('ka_conversions', JSON.stringify(convs));
  }

  /**
   * Génère un QR code de réception pour un wallet.
   * Le patient montre ce QR à un proche (diaspora) pour recevoir des UM.
   */
  function generateReceiveQR(role) {
    const wallet = getWallet(role);
    const payload = {
      type: 'wallet_receive',
      walletId: wallet.walletId,
      role: role,
      timestamp: Date.now(),
      expires: Date.now() + QR_EXPIRY_MS,
    };
    return typeof KA_BRIDGE !== 'undefined' ? KA_BRIDGE.generateTransferCode(payload) : JSON.stringify(payload);
  }

  /**
   * Génère un QR code de paiement (patient → prestataire).
   * Contient le montant + le walletId du destinataire.
   */
  function generatePaymentQR(payerRole, amount, description) {
    const wallet = getWallet(payerRole);
    const payload = {
      type: 'wallet_payment',
      fromRole: payerRole,
      walletId: wallet.walletId,
      amount: amount,
      description: description,
      timestamp: Date.now(),
      expires: Date.now() + QR_EXPIRY_MS,
    };
    return typeof KA_BRIDGE !== 'undefined' ? KA_BRIDGE.generateTransferCode(payload) : JSON.stringify(payload);
  }

  /**
   * Vérifie le solde mensuel solidarité (anti-blanchiment).
   */
  function checkMonthlySolidariteLimit() {
    const ledger = getLedger();
    const now = new Date();
    const thisMonth = now.getMonth();
    const thisYear = now.getFullYear();
    let total = 0;
    for (const tx of ledger) {
      if (tx.type === 'solidarite_credit') {
        const d = new Date(tx.timestamp);
        if (d.getMonth() === thisMonth && d.getFullYear() === thisYear) {
          total += tx.amount;
        }
      }
    }
    return { total, limit: MAX_MONTHLY_SOLIDARITE, ok: total < MAX_MONTHLY_SOLIDARITE };
  }

  // ═══ API PUBLIQUE ═══
  return {
    UM_TO_EUR, UM_TO_CFA, QR_EXPIRY_MS, MAX_MONTHLY_SOLIDARITE,
    getLedger, getWallet, saveWallet,
    credit, debit, requestConversion,
    getConversions, saveConversions,
    generateReceiveQR, generatePaymentQR,
    checkMonthlySolidariteLimit,
    recordTransaction,
  };
})();

// Export global
if (typeof window !== 'undefined') window.KA_WALLET = KA_WALLET;
