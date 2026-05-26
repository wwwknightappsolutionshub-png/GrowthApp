import { notifications } from '@/lib/api-client'

function urlBase64ToArrayBuffer(base64String: string): ArrayBuffer {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)
  for (let i = 0; i < rawData.length; i += 1) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray.buffer as ArrayBuffer
}

export type PushSubscribeResult =
  | { ok: true; message: string }
  | { ok: false; message: string; skipped?: boolean }

const AUTO_PUSH_KEY = 'cf:pwa:auto-push-attempted'

/** Request notification permission and upsert push subscription (idempotent). */
export async function enablePushAutomatically(options?: {
  force?: boolean
  silent?: boolean
}): Promise<PushSubscribeResult> {
  if (typeof window === 'undefined') {
    return { ok: false, message: 'Not in browser', skipped: true }
  }
  if (!('Notification' in window) || !('PushManager' in window) || !('serviceWorker' in navigator)) {
    return { ok: false, message: 'Push is not supported on this device.', skipped: true }
  }
  if (!options?.force && window.localStorage.getItem(AUTO_PUSH_KEY) === '1') {
    return { ok: false, message: 'Push already attempted on this device.', skipped: true }
  }

  try {
    const keyRes = await notifications.pushPublicKey()
    if (!keyRes.data.configured || !keyRes.data.public_key) {
      return { ok: false, message: 'Push is not configured on this server yet.', skipped: true }
    }

    let permission = Notification.permission
    if (permission === 'default') {
      permission = await Notification.requestPermission()
    }
    if (permission !== 'granted') {
      window.localStorage.setItem(AUTO_PUSH_KEY, '1')
      return { ok: false, message: 'Notifications were not allowed.' }
    }

    const registration = await navigator.serviceWorker.ready
    const subscription =
      (await registration.pushManager.getSubscription()) ||
      (await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToArrayBuffer(keyRes.data.public_key),
      }))

    const json = subscription.toJSON()
    await notifications.upsertPushSubscription({
      endpoint: json.endpoint || subscription.endpoint,
      keys: {
        p256dh: json.keys?.p256dh || '',
        auth: json.keys?.auth || '',
      },
      user_agent: window.navigator.userAgent,
    })

    window.localStorage.setItem(AUTO_PUSH_KEY, '1')
    return {
      ok: true,
      message: options?.silent
        ? 'Push alerts enabled.'
        : 'Push alerts enabled — get pinged when a new lead arrives or a booking is due.',
    }
  } catch {
    window.localStorage.setItem(AUTO_PUSH_KEY, '1')
    return { ok: false, message: 'Could not enable push alerts on this device.' }
  }
}
