// KA Phone — Service Worker
// Cache l'application pour le mode hors-ligne

const CACHE_NAME = 'ka-phone-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/ka_index.html',
  '/manifest.json',
  '/sw.js',
  '/icons/ka-192.png',
  '/icons/ka-512.png'
];

// Installation : pré-cache des assets essentiels
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(ASSETS_TO_CACHE).catch(() => {
        // Continue même si certains assets manquent
      });
    })
  );
  self.skipWaiting();
});

// Activation : nettoyage des anciens caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Stratégie : Network First, puis cache
self.addEventListener('fetch', event => {
  // Ignorer les requêtes API (POST)
  if (event.request.url.includes('/api/')) {
    return; // Laisser passer les appels API normalement
  }
  
  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Mettre en cache les réponses réussies
        if (response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // Hors ligne : servir depuis le cache
        return caches.match(event.request).then(cached => {
          return cached || new Response('Mode hors-ligne — KA Phone', {
            status: 503,
            statusText: 'Hors ligne'
          });
        });
      })
  );
});
