import { getPushConfig, subscribePush, unsubscribePush } from '../api/client'

function urlBase64ToUint8Array(base64: string): Uint8Array {
  const padding = '='.repeat((4 - (base64.length % 4)) % 4)
  const raw = atob((base64 + padding).replace(/-/g, '+').replace(/_/g, '/'))
  const out = new Uint8Array(raw.length)
  for (let i = 0; i < raw.length; i += 1) out[i] = raw.charCodeAt(i)
  return out
}

export function pushSupported(): boolean {
  return (
    typeof window !== 'undefined' &&
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    'Notification' in window
  )
}

async function serviceWorkerRegistration(): Promise<ServiceWorkerRegistration> {
  const existing = await navigator.serviceWorker.getRegistration()
  if (existing) return existing
  return await Promise.race([
    navigator.serviceWorker.ready,
    new Promise<ServiceWorkerRegistration>((_, reject) => {
      window.setTimeout(() => {
        reject(
          new Error(
            'App-Hintergrunddienst fehlt. Seite neu laden oder die App auf den Bildschirm legen.',
          ),
        )
      }, 4000)
    }),
  ])
}

export async function currentPushEndpoint(): Promise<string | null> {
  if (!pushSupported()) return null
  try {
    const reg = await serviceWorkerRegistration()
    const sub = await reg.pushManager.getSubscription()
    return sub?.endpoint || null
  } catch {
    return null
  }
}

export async function enablePushOnDevice(): Promise<void> {
  if (!pushSupported()) throw new Error('Hinweise sind auf diesem Gerät nicht verfügbar.')
  const cfg = await getPushConfig()
  if (!cfg.enabled || !cfg.publicKey) {
    throw new Error('Hinweise sind hier noch nicht eingerichtet.')
  }
  const perm = await Notification.requestPermission()
  if (perm !== 'granted') throw new Error('Hinweise wurden nicht erlaubt.')
  const reg = await serviceWorkerRegistration()
  const sub = await reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(cfg.publicKey) as BufferSource,
  })
  const json = sub.toJSON()
  const p256dh = json.keys?.p256dh
  const auth = json.keys?.auth
  if (!json.endpoint || !p256dh || !auth) {
    throw new Error('Abo unvollständig.')
  }
  await subscribePush({ endpoint: json.endpoint, p256dh, auth })
}

export async function disablePushOnDevice(): Promise<void> {
  if (!pushSupported()) return
  let reg: ServiceWorkerRegistration
  try {
    reg = await serviceWorkerRegistration()
  } catch {
    return
  }
  const sub = await reg.pushManager.getSubscription()
  if (sub?.endpoint) {
    await unsubscribePush(sub.endpoint).catch(() => {})
    await sub.unsubscribe().catch(() => {})
  }
}
