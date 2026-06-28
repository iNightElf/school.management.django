const CACHE = 'alrawa-v6';
const PRECACHE_URLS = ['manifest.json'];

self.addEventListener('install', (e) => {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(PRECACHE_URLS).catch(() => {}))
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    Promise.all([
      caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))),
      self.clients.claim(),
    ])
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET' || e.request.url.includes('/api/')) return;
  if (!e.request.url.startsWith('http')) return;

  // ponytail: always fetch index.html from network first
  if (e.request.mode === 'navigate') {
    e.respondWith(
      fetch(e.request).then((response) => {
        if (response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE).then((cache) => cache.put(e.request, clone));
        }
        return response;
      }).catch(async () => {
        const cached = await caches.match(e.request);
        return cached || new Response('Offline', { status: 503, headers: { 'Content-Type': 'text/plain' } });
      })
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then((cached) => cached || fetch(e.request).then((response) => {
      if (response.status === 200) {
        const clone = response.clone();
        caches.open(CACHE).then((cache) => cache.put(e.request, clone));
      }
      return response;
    }).catch(() => new Response('Offline', { status: 503, headers: { 'Content-Type': 'text/plain' } })))
  );
});
