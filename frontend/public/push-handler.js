/* Phase 5: Push-Handler. Ohne Payload keine Meldung (5.1 sendet noch nichts). */
self.addEventListener('push', (event) => {
  let data = {}
  try {
    data = event.data ? event.data.json() : {}
  } catch {
    data = {}
  }
  const title = String(data.title || '').trim()
  const body = String(data.body || '').trim()
  if (!title && !body) return
  event.waitUntil(
    self.registration.showNotification(title || 'Freiraum', {
      body,
      icon: '/pwa-192.svg',
      badge: '/pwa-192.svg',
      data: { url: data.url || '/aufgaben' },
    }),
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const url = (event.notification && event.notification.data && event.notification.data.url) || '/aufgaben'
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if ('focus' in client) {
          client.navigate?.(url)
          return client.focus()
        }
      }
      if (self.clients.openWindow) return self.clients.openWindow(url)
      return undefined
    }),
  )
})
