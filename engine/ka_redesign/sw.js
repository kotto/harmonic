/**
 * KA Phone — Service Worker
 * ==========================
 * Stratégie:
 *   • Pages HTML  → network-first (toujours voir la dernière version)
 *   • API         → network-first (jamais de cache)
 *   • Assets stat → cache-first (performance)
 */

const CACHE_NAME = 'ka-phone-v3';

const STATIC_ASSETS = [
  '/manifest.json',
  '/icons/ka-192.svg',
  '/icons/ka-512.svg',
];

// Installation : pré-cache des assets statiques
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('SW: pre-cache partiel:', err);
      });
    })
  );
  self.skipWaiting();
});

// Activation : purge des anciens caches (v1, v2...)
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

// Fetch
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // API : network-first, jamais de cache
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

  // Pages HTML (navigation) : NETWORK-FIRST → toujours la dernière version
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Mettre à jour le cache avec la nouvelle page
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          return response;
        })
        .catch(() => caches.match(event.request)) // offline → cache
    );
    return;
  }

  // Assets statiques : cache-first, mise à jour en arrière-plan
  event.respondWith(
    caches.match(event.request).then((cached) => {
      const fetchPromise = fetch(event.request).then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      });
      return cached || fetchPromise;
    })
  );
});
