/* ══════════════════════════════════════════════════════════════════════════
   KA LLM AGENT — Moteur de raisonnement local + extraction d'intentions
   ══════════════════════════════════════════════════════════════════════════
   Remplace un LLM cloud par un moteur local hybride :
   - Côté client : extraction d'entités/règles (regex + patterns)
   - Côté serveur (ka_server.py) : /api/ask pour raisonnement complexe
   - Fallback : patterns locaux si serveur indisponible

   Actions supportées :
   - call / sms / contacts
   - diskSpace / battery / deviceInfo / wifiInfo
   - openApp / listApps
   - question générale (délégation au serveur KA)
   ══════════════════════════════════════════════════════════════════════════ */
(function (global) {
  'use strict';

  // ═══════════════════════════════════════════════════════════════════════
  // CONFIGURATION
  // ═══════════════════════════════════════════════════════════════════════
  var CONFIG = {
    apiUrl: null,           // sera défini via localStorage 'ka_api_url'
    timeout: 10000,         // timeout requêtes serveur
    useServer: true,        // essayer serveur d'abord
    debug: false
  };

  // ═══════════════════════════════════════════════════════════════════════
  // PATTERNS D'INTENTIONS (ordre = priorité)
  // ═══════════════════════════════════════════════════════════════════════
  var INTENT_PATTERNS = [
    // Appel téléphonique
    {
      name: 'call',
      patterns: [
        /\b(appelle|appel|téléphone|telephone|contacte)\b.*?(\+?\d[\d\s\-]{8,})/i,
        /\b(appelle|appel|téléphone|telephone|contacte)\b.*?(\b\d{10}\b)/i,
        /\b(numéro|numero)\b.*?(\+?\d[\d\s\-]{8,})/i
      ],
      extract: function (text, match) {
        var num = match[2] || match[1];
        return { action: 'call', number: num.replace(/\s+/g, ''), originalText: text };
      }
    },
    // SMS
    {
      name: 'sms',
      patterns: [
        /\b(envoie|envoi|envois|envoie-moi|send)\b.*?(sms|message|texto)\b.*?(?:à|a|au|à\s+)\s*([^,.]+).*?(?:que|:)\s*(.+)/i,
        /\b(sms|message|texto)\b.*?(?:à|a|au|à\s+)\s*([^,.]+).*?(?:que|:)\s*(.+)/i,
        /\b(texte|text)\b.*?(\+?\d[\d\s\-]{8,}).*?(?:que|:)\s*(.+)/i
      ],
      extract: function (text, match) {
        var contact = (match[3] || match[2] || '').trim();
        var msg = (match[4] || match[3] || '').trim();
        return { action: 'sms', contact: contact, text: msg, originalText: text };
      }
    },
    // Contacts (recherche)
    {
      name: 'contacts',
      patterns: [
        /\b(cherche|trouve|recherche|contact)\b.*?(?:de|du|nommé|qui\s+s['']?appelle)\s+([^,.]+)/i,
        /\b(quel\s+est\s+le\s+numéro|numero\s+de)\b\s+([^,.]+)/i
      ],
      extract: function (text, match) {
        return { action: 'contacts', query: (match[1] || match[2] || '').trim(), originalText: text };
      }
    },
    // Espace disque
    {
      name: 'diskSpace',
      patterns: [
        /\b(espace|disque|stockage|capacité|capacite)\b.*?(libre|disponible|restant)/i,
        /\b(combien.*(?:go|mo|gb|mb).*libre|disque.*plein)/i,
        /\b(place|espace).*(restant|libre)/i
      ],
      extract: function (text) { return { action: 'diskSpace', originalText: text }; }
    },
    // Batterie
    {
      name: 'battery',
      patterns: [
        /\b(batterie|battery|charge)\b.*?(niveau|pourcent|restant|combien)/i,
        /\b(combien.*batterie|batterie.*rest)/i
      ],
      extract: function (text) { return { action: 'battery', originalText: text }; }
    },
    // Infos appareil
    {
      name: 'deviceInfo',
      patterns: [
        /\b(modèle|modele|marque|version|android|sdk|device|téléphone|telephone)\b.*?(quel|quelle|comment|info)/i,
        /\b(infos?|informations?)\b.*?(téléphone|telephone|appareil|device)/i
      ],
      extract: function (text) { return { action: 'deviceInfo', originalText: text }; }
    },
    // WiFi
    {
      name: 'wifiInfo',
      patterns: [
        /\b(wifi|wi-fi|wi fi|réseau|reseau)\b.*?(ssid|nom|force|signal|ip|connecté|connecte)/i,
        /\b(quel.*wifi|wifi.*quel)/i
      ],
      extract: function (text) { return { action: 'wifiInfo', originalText: text }; }
    },
    // Lancer app
    {
      name: 'openApp',
      patterns: [
        /\b(ouvre|lance|démarre|demarre|start)\b\s+([a-zA-Zà-ÿ0-9\s]+)/i,
        /\b(ouvre|lance)\b.*?(l'application|l'appli|l'appli\s+)\s*([^,.]+)/i
      ],
      extract: function (text, match) {
        var appName = (match[2] || match[3] || '').trim().toLowerCase();
        return { action: 'openApp', appName: appName, originalText: text };
      }
    },
    // Lister apps
    {
      name: 'listApps',
      patterns: [
        /\b(liste|affiche|montre)\b.*?(applications?|applis?|apps?)\b/i,
        /\b(quelles?\s+applis?|apps?\s+install)/i
      ],
      extract: function (text) { return { action: 'listApps', originalText: text }; }
    }
  ];

  // ═══════════════════════════════════════════════════════════════════════
  // RÉSOLUTION CONTACT → NUMÉRO (via plugin contacts)
  // ═══════════════════════════════════════════════════════════════════════
  function resolveContact(contactName) {
    if (!window.KA_Native || !window.KA_Native.contacts) return Promise.resolve(null);
    return window.KA_Native.contacts(contactName)
      .then(function (r) {
        if (r && r.contacts && r.contacts.length > 0) {
          // Prendre le premier match
          return r.contacts[0].number;
        }
        return null;
      })
      .catch(function () { return null; });
  }

  // ═══════════════════════════════════════════════════════════════════════
  // DÉTECTION D'INTENTION
  // ═══════════════════════════════════════════════════════════════════════
  function detectIntent(text) {
    text = String(text).trim().toLowerCase();
    for (var i = 0; i < INTENT_PATTERNS.length; i++) {
      var intent = INTENT_PATTERNS[i];
      for (var j = 0; j < intent.patterns.length; j++) {
        var match = text.match(intent.patterns[j]);
        if (match) {
          return intent.extract(text, match);
        }
      }
    }
    // Aucun pattern → question générale
    return { action: 'ask', question: text, originalText: text };
  }

  // ═══════════════════════════════════════════════════════════════════════
  // EXÉCUTION D'ACTION
  // ═══════════════════════════════════════════════════════════════════════
  function executeAction(intent) {
    var KA = window.KA_Native;
    if (!KA || !KA.isNative()) {
      return Promise.resolve({ response: 'Actions natives non disponibles (pas sur Android)', fallback: true });
    }

    switch (intent.action) {
      case 'call':
        var num = intent.number;
        if (!/^\+?\d+$/.test(num)) {
          // Essayer de résoudre via contact
          return resolveContact(intent.contact || num).then(function (resolved) {
            if (resolved) return KA.call(resolved);
            return { response: 'Numéro invalide ou contact non trouvé: ' + num, error: true };
          });
        }
        return KA.call(num).then(function () {
          return { response: 'Appel lancé vers ' + num };
        });

      case 'sms':
        if (intent.contact && !intent.text.match(/^\+?\d+$/)) {
          return resolveContact(intent.contact).then(function (num) {
            if (num) return KA.sms(num, intent.text);
            return { response: 'Contact non trouvé: ' + intent.contact, error: true };
          });
        }
        return KA.sms(intent.contact || '', intent.text).then(function () {
          return { response: 'SMS prêt à être envoyé à ' + intent.contact };
        });

      case 'contacts':
        return KA.contacts(intent.query).then(function (r) {
          if (r && r.contacts && r.contacts.length) {
            var list = r.contacts.slice(0, 5).map(function (c) { return c.name + ' (' + c.number + ')'; }).join(', ');
            return { response: 'Contacts trouvés: ' + list, data: r.contacts };
          }
          return { response: 'Aucun contact trouvé pour: ' + intent.query };
        });

      case 'diskSpace':
        return KA.diskSpace().then(function (r) {
          return { response: 'Espace disque: ' + r.freeGB + ' GB libre sur ' + r.totalGB + ' GB (' + r.percentUsed + '% utilisé)', data: r };
        });

      case 'battery':
        return KA.battery().then(function (r) {
          var state = r.isCharging ? 'en charge' : r.status;
          return { response: 'Batterie: ' + r.level + '% (' + state + ')', data: r };
        });

      case 'deviceInfo':
        return KA.deviceInfo().then(function (r) {
          return { response: 'Appareil: ' + r.model + ' (' + r.manufacturer + '), Android ' + r.androidVersion, data: r };
        });

      case 'wifiInfo':
        return KA.wifiInfo().then(function (r) {
          if (r.isConnected) {
            return { response: 'WiFi: ' + r.ssid + ' (' + r.rssi + ' dBm, ' + r.linkSpeed + ' Mbps)', data: r };
          }
          return { response: 'WiFi non connecté', data: r };
        });

      case 'openApp':
        // Résoudre nom app → packageName via listApps
        return KA.listApps({ includeSystem: false }).then(function (r) {
          if (r && r.apps) {
            var app = r.apps.find(function (a) { return a.name.toLowerCase().includes(intent.appName); });
            if (app) return KA.openApp(app.packageName).then(function () { return { response: 'Ouverture de ' + app.name }; });
          }
          return { response: 'Application non trouvée: ' + intent.appName, error: true };
        });

      case 'listApps':
        return KA.listApps({ includeSystem: false }).then(function (r) {
          if (r && r.apps && r.apps.length) {
            var list = r.apps.slice(0, 10).map(function (a) { return a.name; }).join(', ');
            return { response: 'Applications: ' + list + (r.apps.length > 10 ? '...' : ''), data: r.apps };
          }
          return { response: 'Aucune application trouvée' };
        });

      case 'ask':
      default:
        // Déléguer au serveur KA
        return askServer(intent.question);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // QUESTION SERVEUR KA (/api/ask)
  // ═══════════════════════════════════════════════════════════════════════
  function getApiUrl() {
    if (CONFIG.apiUrl) return CONFIG.apiUrl;
    try {
      var u = localStorage.getItem('ka_api_url');
      if (u) return CONFIG.apiUrl = u;
    } catch (e) {}
    // Fallback : même hôte que la page
    if (typeof location !== 'undefined' && location.hostname) {
      return CONFIG.apiUrl = 'http://' + location.hostname + ':8765';
    }
    return CONFIG.apiUrl = 'http://localhost:8765';
  }

  function askServer(question) {
    if (!CONFIG.useServer) return Promise.resolve({ response: 'Serveur désactivé', fallback: true });
    var url = getApiUrl() + '/api/ask';
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: question, style: 'concise' }),
      signal: AbortSignal.timeout(CONFIG.timeout)
    })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (d) { return { response: d.response || d.text || d.answer || 'Pas de réponse', server: true }; })
      .catch(function (e) {
        console.warn('[KA_LLM_AGENT] Serveur indisponible:', e.message);
        return { response: 'Je ne peux pas répondre pour le moment (serveur indisponible).', fallback: true };
      });
  }

  // ═══════════════════════════════════════════════════════════════════════
  // API PUBLIQUE
  // ═══════════════════════════════════════════════════════════════════════
  var KA_LLM_AGENT = {
    CONFIG: CONFIG,

    // Traiter une entrée utilisateur (texte ou voix)
    process: function (input) {
      var intent = detectIntent(input);
      if (CONFIG.debug) console.log('[KA_LLM_AGENT] Intent:', intent);
      return executeAction(intent).then(function (result) {
        return {
          intent: intent,
          response: result.response,
          data: result.data,
          error: result.error,
          server: result.server,
          fallback: result.fallback
        };
      });
    },

    // Raccourci pour questions directes serveur
    ask: function (question) { return askServer(question); },

    // Config
    setApiUrl: function (url) { CONFIG.apiUrl = url; },
    setDebug: function (on) { CONFIG.debug = !!on; },
    useServer: function (on) { CONFIG.useServer = !!on; }
  };

  global.KA_LLM_AGENT = KA_LLM_AGENT;

  if (global.console && console.log) console.log('KA · LLM Agent local chargé (intentions + actions natives)');

})(typeof window !== 'undefined' ? window : this);