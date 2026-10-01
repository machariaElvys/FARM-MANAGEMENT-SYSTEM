const CACHE_NAME = 'shamba-ledger-shell-v2'

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      const response = await fetch('/')
      if (!response.ok) throw new Error('Could not cache the app shell.')
      const html = await response.clone().text()
      await cache.put('/', response)
      const assets = [...html.matchAll(/(?:src|href)=["']([^"']+\.(?:js|jsx|css))(?:\?[^"']*)?["']/g)]
        .map((match) => new URL(match[1], self.location.origin).href)
        .filter((url) => new URL(url).origin === self.location.origin)
      if (assets.length) await cache.addAll(assets)
    }).then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (event) => {
  const request = event.request
  const url = new URL(request.url)
  if (request.method !== 'GET' || url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return

  if (request.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        return await fetch(request)
      } catch {
        return (await caches.match('/')) || Response.error()
      }
    })())
    return
  }

  async function fetchAndCache() {
    const response = await fetch(request)
    if (response.ok) {
      const copy = response.clone()
      try {
        const cache = await caches.open(CACHE_NAME)
        await cache.put(request, copy)
      } catch {
        // Caching is best effort; a successful network response should still render.
      }
    }
    return response
  }

  event.respondWith((async () => {
    const cached = await caches.match(request)
    try {
      return await fetchAndCache()
    } catch {
      return cached || Response.error()
    }
  })())
})
