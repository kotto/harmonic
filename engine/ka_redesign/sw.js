/**
 * KA Phone — Service Worker
 * ==========================
 * Stratégie: Network-first pour l'API, Cache-first pour les assets statiques
 */

const CACHE_NAME = 'ka-phone-v2';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/css/theme.css',
  '/js/api.js',
  '/js/app.js',
  '/manifest.json',
  '/screens/home.html',
  '/screens/chat.html',
  '/screens/code.html',
  '/screens/memory.html',
  '/screens/jlens.html',
  '/screens/health.html',
  '/screens/store.html',
  '/screens/profile.html',
  '/screens/enterprise.html',
  '/screens/storage.html',
  '/screens/creative.html',
  '/screens/onboarding.html',
];

// Installation: pré-cache des assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE).catch((err) => {
        console.warn('SW: Some assets failed to pre-cache:', err);
      });
    })
  );
  self.skipWaiting();
});

// Activation: nettoyage des anciens caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      );
    })
  );
  self.clients.claim();
});

// Fetch: stratégie hybride
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // API calls: Network-first (pas de cache)
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/v1/')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(JSON.stringify({ error: 'offline' }), {
          status: 503,
          headers: { 'Content-Type': 'application/json' }
        });
      })
    );
    return;
  }

  // Static assets: Cache-first, puis network fallback
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, clone);
          });
        }
        return response;
      });
    })
  );
});
