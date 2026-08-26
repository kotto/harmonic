/**
 * KA Banking — Client serveur KARE (passerelle Ecobank)
 * =======================================================
 * Pont entre le wallet local (KA_WALLET) et le serveur bancaire
 * (/api/banking/*). La source de vérité de l'argent est le SERVEUR ;
 * le localStorage reste un cache hors-ligne réplicable.
 *
 * Auth : signature HMAC-SHA256 du corps (secret partagé) OU clé API.
 * Idempotence : chaque écriture envoie un Idempotency-Key unique.
 *
 * Usage :
 *   KA_BANKING.configure({ baseUrl: 'http://localhost:8765', secret: '...' });
 *   await KA_BANKING.health();
 *   await KA_BANKING.requestConversion({ wallet_id, amount_um, currency });
 *
 * Hors-ligne : les écritures sont mises en file (ka_banking_queue) et
 * rejouées par KA_BANKING.flush() quand la connexion revient.
 */

'use strict';

const KA_BANKING = (() => {
  const config = {
    baseUrl: (typeof VITAL_KA_CONFIG !== 'undefined' && VITAL_KA_CONFIG.serverUrl) || 'http://localhost:8765',
    secret: '',     // secret partagé (HMAC) — sinon X-API-Key
    apiKey: '',     // clé API (fallback)
  };
  const QUEUE_KEY = 'ka_banking_queue';

  function configure(opts) {
    Object.assign(config, opts || {});
    return config;
  }

  function _generateIdemKey() {
    return 'idem_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 10);
  }

  // ── Signature HMAC-SHA256 (Web Crypto) ────────────────────────────────────
  async function _sign(bodyStr) {
    if (!config.secret || typeof crypto === 'undefined' || !crypto.subtle) return '';
    try {
      const enc = new TextEncoder();
      const key = await crypto.subtle.importKey(
        'raw', enc.encode(config.secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
      );
      const sig = await crypto.subtle.sign('HMAC', key, enc.encode(bodyStr));
      return Array.from(new Uint8Array(sig)).map(b => b.toString(16).padStart(2, '0')).join('');
    } catch (e) { return ''; }
  }

  // ── Requête signée + idempotente ──────────────────────────────────────────
  async function request(method, path, body) {
    const idem = _generateIdemKey();
    const bodyStr = body ? JSON.stringify(body) : '{}';
    const headers = { 'Content-Type': 'application/json', 'Idempotency-Key': idem };
    const sig = await _sign(bodyStr);
    if (sig) headers['X-Signature'] = sig;
    if (config.apiKey) headers['X-API-Key'] = config.apiKey;

    const resp = await fetch(config.baseUrl + path, { method, headers, body: bodyStr });
    let data = null;
    try { data = await resp.json(); } catch (e) { data = null; }
    if (!resp.ok) {
      const err = new Error((data && data.error) || ('HTTP ' + resp.status));
      err.status = resp.status;
      err.code = data && data.code;
      throw err;
    }
    return data;
  }

  // ── File hors-ligne ───────────────────────────────────────────────────────
  function _queue() {
    try { return JSON.parse(localStorage.getItem(QUEUE_KEY) || '[]'); } catch (e) { return []; }
  }
  function _saveQueue(q) {
    localStorage.setItem(QUEUE_KEY, JSON.stringify(q));
  }

  async function _safe(method, path, body) {
    try {
      return { ok: true, data: await request(method, path, body) };
    } catch (e) {
      // Réseau / serveur indisponible → on met en file pour rejeu.
      const q = _queue();
      q.push({ method, path, body, queuedAt: new Date().toISOString() });
      _saveQueue(q);
      return { ok: false, offline: true, queued: true, error: String(e && e.message || e) };
    }
  }

  /** Rejoue la file hors-ligne dans l'ordre. Retourne { sent, failed }. */
  async function flush() {
    const q = _queue();
    if (!q.length) return { sent: 0, failed: 0 };
    let sent = 0;
    const remaining = [];
    for (const item of q) {
      try {
        await request(item.method, item.path, item.body);
        sent++;
      } catch (e) {
        remaining.push(item);
      }
    }
    _saveQueue(remaining);
    return { sent, failed: remaining.length };
  }

  // ── API publique (miroir des routes serveur) ──────────────────────────────
  function health() { return request('GET', '/api/banking/health'); }

  function upsertAccount(wallet_id, role, bank_account) {
    return _safe('POST', '/api/banking/accounts', { wallet_id, role, bank_account });
  }

  function getAccount(wallet_id) {
    return request('GET', '/api/banking/accounts/' + encodeURIComponent(wallet_id));
  }

  function collectMomo(amount_fiat, currency, wallet_id, phone) {
    return _safe('POST', '/api/banking/collection/momo',
      { amount_fiat, currency, wallet_id, phone });
  }

  function collectCard(amount_fiat, currency, wallet_id, card) {
    return _safe('POST', '/api/banking/collection/card',
      { amount_fiat, currency, wallet_id, card });
  }

  function requestConversion(wallet_id, amount_um, currency, bank_info) {
    return _safe('POST', '/api/banking/conversion/request',
      { wallet_id, amount_um, currency, bank_info });
  }

  function executeConversion(conversion_id) {
    return _safe('POST', '/api/banking/conversion/' + encodeURIComponent(conversion_id) + '/execute');
  }

  function getConversion(conversion_id) {
    return request('GET', '/api/banking/conversion/' + encodeURIComponent(conversion_id));
  }

  function reconciliation(date_iso) {
    return request('GET', '/api/banking/reconciliation/' + encodeURIComponent(date_iso));
  }

  return {
    configure, request, flush, _queue,
    health, upsertAccount, getAccount,
    collectMomo, collectCard,
    requestConversion, executeConversion, getConversion,
    reconciliation,
  };
})();

// Export global
if (typeof window !== 'undefined') window.KA_BANKING = KA_BANKING;
