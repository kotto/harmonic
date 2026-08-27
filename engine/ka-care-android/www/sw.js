// KA CARE — Service Worker (Offline PWA)
const CACHE='ka-care-v1';
const ASSETS=['/','/index.html','/manifest.json'];

self.addEventListener('install',e=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)));
});

self.addEventListener('fetch',e=>{
  // API calls: network first, no cache
  if(e.request.url.includes('/api/')){
    e.respondWith(fetch(e.request).catch(()=>new Response(
      JSON.stringify({error:'offline'}),{headers:{'Content-Type':'application/json'}})));
    return;
  }
  // Static assets: cache first, then network
  e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));
});
