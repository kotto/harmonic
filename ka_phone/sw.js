/* KA PHONE — Service Worker PWA v5 */
var CACHE_NAME = 'ka-phone-v5-' + Date.now()
var ASSETS = ['/', '/index.html', '/www/ka-ui.css', '/www/ka-ui.js', '/www/manifest.json', '/sw.js']

self.addEventListener('install', function(e) {
  self.skipWaiting()
  e.waitUntil(caches.open(CACHE_NAME).then(function(c) { return c.addAll(ASSETS).catch(function() {}) }))
})

self.addEventListener('activate', function(e) {
  e.waitUntil(caches.keys().then(function(names) {
    return Promise.all(names.map(function(n) { if (n !== CACHE_NAME) return caches.delete(n) }))
  }))
  return self.clients.claim()
})

self.addEventListener('fetch', function(e) {
  if (e.request.method !== 'GET') return
  if (e.request.url.indexOf('/api/') !== -1) {
    e.respondWith(fetch(e.request).catch(function() {
      return new Response(JSON.stringify({ error: 'hors_ligne', message: 'KA Phone — Mode hors-ligne actif', hors_ligne: true }), { status: 503, headers: { 'Content-Type': 'application/json' } })
    }))
    return
  }
  e.respondWith(fetch(e.request).then(function(r) {
    var r2 = r.clone()
    caches.open(CACHE_NAME).then(function(c) { c.put(e.request, r2) })
    return r
  }).catch(function() {
    return caches.match(e.request).then(function(cr) {
      if (cr) return cr
      if (e.request.mode === 'navigate') return caches.match('/index.html')
      return new Response('Hors ligne', { status: 503 })
    })
  }))
})