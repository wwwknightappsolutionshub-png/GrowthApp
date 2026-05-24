'use client'

import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { useLoyaltyBranding } from '@/components/loyalty-portal/LoyaltyBrandingProvider'
import { LoyaltyAuthGate } from '@/components/loyalty-portal/LoyaltyAuthGate'
import { loyaltyPortalCustomer } from '@/lib/api-client'
import { clearLoyaltyToken, rewardsPath } from '@/lib/loyalty-portal-auth'

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

export default function RewardsProfilePage({ params }: { params: { tenant: string } }) {
  const tenant = params.tenant
  const router = useRouter()
  const qc = useQueryClient()
  const { branding } = useLoyaltyBranding()
  const { data } = useQuery({
    queryKey: ['loyalty-me', tenant],
    queryFn: () => loyaltyPortalCustomer.me(tenant).then((r) => r.data),
  })
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [dob, setDob] = useState('')
  const [pushBusy, setPushBusy] = useState(false)

  const savePrefs = useMutation({
    mutationFn: (payload: Parameters<typeof loyaltyPortalCustomer.updatePreferences>[1]) =>
      loyaltyPortalCustomer.updatePreferences(tenant, payload),
    onSuccess: () => {
      toast.success('Preferences saved')
      void qc.invalidateQueries({ queryKey: ['loyalty-me', tenant] })
    },
    onError: () => toast.error('Could not save preferences'),
  })

  const setPw = useMutation({
    mutationFn: () => loyaltyPortalCustomer.setPassword(tenant, password),
    onSuccess: () => {
      toast.success('Password updated')
      setPassword('')
      setConfirm('')
      void qc.invalidateQueries({ queryKey: ['loyalty-me', tenant] })
    },
    onError: () => toast.error('Could not update password'),
  })

  async function togglePush(enabled: boolean) {
    setPushBusy(true)
    try {
      if (!enabled) {
        await loyaltyPortalCustomer.pushUnsubscribe(tenant)
        toast.success('Push notifications disabled')
        void qc.invalidateQueries({ queryKey: ['loyalty-me', tenant] })
        return
      }
      if (!('Notification' in window) || !('PushManager' in window) || !('serviceWorker' in navigator)) {
        toast.error('Push notifications are not supported on this device')
        return
      }
      const keyRes = await loyaltyPortalCustomer.pushPublicKey()
      if (!keyRes.data.configured || !keyRes.data.public_key) {
        toast.error('Push alerts are not configured on this server yet')
        return
      }
      const permission = await window.Notification.requestPermission()
      if (permission !== 'granted') {
        toast.error('Notification permission was denied')
        return
      }
      const registration = await navigator.serviceWorker.register('/rewards/sw.js')
      await navigator.serviceWorker.ready
      const subscription =
        (await registration.pushManager.getSubscription()) ||
        (await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToArrayBuffer(keyRes.data.public_key),
        }))
      const json = subscription.toJSON()
      await loyaltyPortalCustomer.pushSubscribe(tenant, {
        endpoint: json.endpoint || subscription.endpoint,
        keys: {
          p256dh: json.keys?.p256dh || '',
          auth: json.keys?.auth || '',
        },
      })
      toast.success('Push notifications enabled')
      void qc.invalidateQueries({ queryKey: ['loyalty-me', tenant] })
    } catch {
      toast.error('Could not update push notification settings')
    } finally {
      setPushBusy(false)
    }
  }

  function logout() {
    clearLoyaltyToken(tenant)
    router.replace(rewardsPath(tenant, 'login'))
  }

  useEffect(() => {
    if (data?.date_of_birth) {
      setDob(data.date_of_birth.slice(0, 10))
    }
  }, [data?.date_of_birth])

  function togglePref(
    key: 'marketing_email' | 'marketing_sms' | 'birthday_participation' | 'expiring_points_reminders',
    value: boolean,
  ) {
    savePrefs.mutate({ [key]: value })
  }

  return (
    <LoyaltyAuthGate tenant={tenant}>
      <div className="space-y-4">
        <h1 className="text-lg font-semibold">Profile</h1>
        <section className="card space-y-1 text-sm">
          <p>
            <span className="text-slate-500">Name</span>{' '}
            <span className="font-medium">
              {data?.first_name} {data?.last_name ?? ''}
            </span>
          </p>
          {data?.email ? (
            <p>
              <span className="text-slate-500">Email</span>{' '}
              <span className="font-medium">{data.email}</span>
            </p>
          ) : null}
          {data?.phone ? (
            <p>
              <span className="text-slate-500">Phone</span>{' '}
              <span className="font-medium">{data.phone}</span>
            </p>
          ) : null}
          <p>
            <span className="text-slate-500">Business</span>{' '}
            <span className="font-medium">{branding?.tenant_name}</span>
          </p>
        </section>

        <section className="card space-y-3">
          <h2 className="text-sm font-semibold">Birthday &amp; preferences</h2>
          <label className="block text-xs text-slate-500">
            Date of birth
            <input
              type="date"
              className="input mt-1"
              value={dob}
              onChange={(e) => setDob(e.target.value)}
            />
          </label>
          <button
            type="button"
            className="btn-secondary w-full text-xs"
            disabled={savePrefs.isPending}
            onClick={() => savePrefs.mutate({ date_of_birth: dob || null })}
          >
            Save birthday
          </button>
          <p className="text-xs text-slate-500">
            Add your birthday to receive a yearly bonus points gift from {branding?.tenant_name}.
          </p>

          {[
            {
              key: 'marketing_email' as const,
              label: 'Marketing emails',
              hint: 'Offers and promotions by email.',
              value: data?.marketing_email ?? true,
            },
            {
              key: 'marketing_sms' as const,
              label: 'Marketing SMS',
              hint: 'Text message offers (when available).',
              value: data?.marketing_sms ?? false,
            },
            {
              key: 'birthday_participation' as const,
              label: 'Birthday rewards',
              hint: 'Receive your annual birthday points bonus.',
              value: data?.birthday_participation ?? true,
            },
            {
              key: 'expiring_points_reminders' as const,
              label: 'Expiring points reminders',
              hint: 'Get notified before points expire.',
              value: data?.expiring_points_reminders ?? true,
            },
          ].map((pref) => (
            <div key={pref.key} className="flex items-center justify-between gap-3 border-t border-slate-100 pt-3">
              <div>
                <p className="text-sm font-medium">{pref.label}</p>
                <p className="text-xs text-slate-500">{pref.hint}</p>
              </div>
              <button
                type="button"
                className="btn-secondary shrink-0 text-xs"
                disabled={savePrefs.isPending}
                onClick={() => togglePref(pref.key, !pref.value)}
              >
                {pref.value ? 'On' : 'Off'}
              </button>
            </div>
          ))}
        </section>

        <section className="card flex items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold">Push notifications</h2>
            <p className="mt-1 text-xs text-slate-500">
              Get alerts for points, rewards, and tier upgrades.
            </p>
          </div>
          <button
            type="button"
            className="btn-secondary shrink-0 text-xs"
            disabled={pushBusy}
            onClick={() => void togglePush(!data?.push_notifications_enabled)}
          >
            {data?.push_notifications_enabled ? 'Disable' : 'Enable'}
          </button>
        </section>

        {data?.must_change_password ? (
          <section className="card space-y-3">
            <h2 className="text-sm font-semibold">Set a new password</h2>
            <input
              type="password"
              className="input"
              placeholder="New password (min 8 chars)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <input
              type="password"
              className="input"
              placeholder="Confirm password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
            />
            <button
              type="button"
              className="btn-primary w-full"
              disabled={password.length < 8 || password !== confirm || setPw.isPending}
              onClick={() => setPw.mutate()}
            >
              Save password
            </button>
          </section>
        ) : null}

        <button type="button" className="btn-secondary w-full" onClick={logout}>
          Sign out
        </button>
      </div>
    </LoyaltyAuthGate>
  )
}
