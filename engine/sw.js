/* ══════════════════════════════════════════════════════════════════════════
   VITAL KA — Service Worker v3
   ══════════════════════════════════════════════════════════════════════════
   Stratégie :
     • Navigation (HTML)   → network-first, repli cache si hors-ligne
     • Assets statiques    → cache-first, mise à jour en arrière-plan
     • API / cross-origin  → réseau direct, JAMAIS mis en cache
       (les réponses du serveur vocal :8420 ne doivent jamais être cachées)
   ══════════════════════════════════════════════════════════════════════════ */
const CACHE = 'vital-ka-v3';

// Cœur applicatif pré-caché à l'installation (mode hors-ligne complet)
const CORE = [
  '/vital_ka.html',
  '/ka_patient.html',
  '/manifest.json',
  '/logo2.jpg',
  '/vital_ka.css',
  '/vital_ka_ai.css',
  '/ka_telemedecine.css',
  '/vital_ka_config.js',
  '/ka_core.js',
  '/ka_secure.js',
  '/ka_bridge.js',
  '/ka_hcv.js',
  '/ka_network.js',
  '/ka_care_voice.js',
  '/ka_telemedecine.js',
  '/vital_ka_hologram.js',
  '/vital_ka_knowledge.js',
  '/vital_ka_voice.js',
  '/vital_ka_stt.js',
  '/vital_ka_dialogue.js',
  '/vital_ka_conversation.js',
  '/vital_ka_ble.js',
  '/vital_ka_ai.js',
  '/vital_ka_app.js',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((cache) =>
      // Pré-cache best-effort : un asset manquant ne bloque pas l'installation
      Promise.allSettled(CORE.map((url) => cache.add(url)))
    )
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  const req = e.request;

  // 1. Non-GET → réseau direct (POST synthèse vocale, etc.)
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // 2. Cross-origin (serveur vocal :8420, CDN fonts) → réseau direct, pas de cache
  if (url.origin !== self.location.origin) return;

  // 3. Navigation HTML → network-first (fraîcheur), repli cache hors-ligne
  if (req.mode === 'navigate' || req.destination === 'document') {
    e.respondWith(
      fetch(req)
        .then((resp) => {
          if (resp.ok) {
            const clone = resp.clone();
            caches.open(CACHE).then((c) => c.put(req, clone));
          }
          return resp;
        })
        .catch(() => caches.match(req).then((c) => c || caches.match('/vital_ka.html')))
    );
    return;
  }

  // 4. Assets statiques same-origin → cache-first + mise à jour arrière-plan
  e.respondWith(
    caches.match(req).then((cached) => {
      const network = fetch(req)
        .then((resp) => {
          if (resp.ok) {
            const clone = resp.clone();
            caches.open(CACHE).then((c) => c.put(req, clone));
          }
          return resp;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
