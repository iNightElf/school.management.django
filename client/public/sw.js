const CACHE = 'alrawa-v5';
const PRECACHE_URLS = ['./', 'manifest.json'];

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

  e.respondWith(
    caches.match(e.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(e.request).then((response) => {
        if (!response || response.status !== 200) {
          return response;
        }
        const responseToCache = response.clone();
        caches.open(CACHE).then((cache) => {
          cache.put(e.request, responseToCache);
        });
        return response;
      }).catch(() => {
        return new Response('Offline', { status: 503, headers: { 'Content-Type': 'text/plain' } });
      });
    })
  );
});
