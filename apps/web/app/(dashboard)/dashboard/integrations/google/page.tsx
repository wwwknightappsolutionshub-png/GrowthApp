'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'next/navigation'
import { ArrowLeft, ExternalLink, RefreshCw, Unplug } from 'lucide-react'
import { toast } from 'sonner'
import { integrations } from '@/lib/api-client'

interface GoogleCredentials {
  registered: boolean
  status: string | null
  redirect_uri: string
  google_client_id: string | null
  connected_at: string | null
  expires_at: string | null
}

interface GoogleStatus {
  connected: boolean
  configured: boolean
  location_title: string | null
  last_sync_at: string | null
  available_locations: { name: string; title: string }[]
}

export default function GoogleIntegrationsPage() {
  const qc = useQueryClient()
  const searchParams = useSearchParams()
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const [pickLocation, setPickLocation] = useState('')

  const credentials = useQuery<GoogleCredentials>({
    queryKey: ['integrations', 'google', 'credentials'],
    queryFn: () => integrations.googleCredentials().then((r) => r.data),
  })

  const status = useQuery<GoogleStatus>({
    queryKey: ['integrations', 'google', 'status'],
    queryFn: () => integrations.googleStatus().then((r) => r.data),
  })

  useEffect(() => {
    const google = searchParams.get('google')
    if (google === 'connected') {
      toast.success('Google Business Profile connected')
      qc.invalidateQueries({ queryKey: ['integrations', 'google'] })
    } else if (google === 'error') {
      toast.error('Google connection failed')
    }
  }, [searchParams, qc])

  const register = useMutation({
    mutationFn: () =>
      integrations.googleRegisterCredentials({
        google_client_id: clientId,
        google_client_secret: clientSecret,
      }),
    onSuccess: () => {
      toast.success('Google credentials saved')
      qc.invalidateQueries({ queryKey: ['integrations', 'google'] })
    },
    onError: () => toast.error('Could not save credentials'),
  })

  const connect = useMutation({
    mutationFn: () => integrations.googleAuthUrl(),
    onSuccess: (res) => {
      window.location.href = res.data.url
    },
    onError: () => toast.error('Could not start Google OAuth'),
  })

  const refresh = useMutation({
    mutationFn: () => integrations.googleRefreshToken(),
    onSuccess: () => {
      toast.success('Token refreshed')
      qc.invalidateQueries({ queryKey: ['integrations', 'google'] })
    },
    onError: () => toast.error('Refresh failed — reconnect if needed'),
  })

  const syncReviews = useMutation({
    mutationFn: () => integrations.googleReviewsSync(),
    onSuccess: (res) => toast.success(`Synced ${res.data.total_fetched} reviews`),
    onError: () => toast.error('Review sync failed'),
  })

  const disconnect = useMutation({
    mutationFn: () => integrations.googleDisconnect(),
    onSuccess: () => {
      toast.success('Google disconnected')
      qc.invalidateQueries({ queryKey: ['integrations', 'google'] })
    },
  })

  const selectLocation = useMutation({
    mutationFn: (location_name: string) => integrations.googleSelectLocation(location_name),
    onSuccess: () => {
      toast.success('Location updated')
      qc.invalidateQueries({ queryKey: ['integrations', 'google'] })
    },
  })

  const creds = credentials.data
  const conn = status.data
  const locations = conn?.available_locations ?? []

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/dashboard/integrations"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-3"
        >
          <ArrowLeft className="h-4 w-4" />
          All integrations
        </Link>
        <h1 className="text-2xl font-bold text-foreground">Google Business Profile</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Connect using your own Google Cloud OAuth app. CustomerFlow never needs Google verification.
        </p>
      </div>

      <div className="rounded-xl border bg-card p-6 space-y-4">
        <h2 className="font-semibold">1. Register your Google Cloud app</h2>
        <p className="text-sm text-muted-foreground">
          Create OAuth credentials in Google Cloud Console and paste them below.
        </p>
        <div className="grid gap-3 md:grid-cols-2">
          <label className="text-sm space-y-1">
            <span className="text-muted-foreground">Google Client ID</span>
            <input
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder={creds?.google_client_id ?? 'xxxx.apps.googleusercontent.com'}
              className="w-full rounded-lg border px-3 py-2 bg-background"
            />
          </label>
          <label className="text-sm space-y-1">
            <span className="text-muted-foreground">Google Client Secret</span>
            <input
              type="password"
              value={clientSecret}
              onChange={(e) => setClientSecret(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-lg border px-3 py-2 bg-background"
            />
          </label>
        </div>
        <label className="text-sm space-y-1 block">
          <span className="text-muted-foreground">Redirect URI (add this in Google Cloud)</span>
          <input
            readOnly
            value={creds?.redirect_uri ?? ''}
            className="w-full rounded-lg border px-3 py-2 bg-muted font-mono text-xs"
          />
        </label>
        <button
          type="button"
          onClick={() => register.mutate()}
          disabled={!clientId || !clientSecret || register.isPending}
          className="rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          Save credentials
        </button>
      </div>

      <div className="rounded-xl border bg-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">2. Connect Google Business Profile</h2>
          <span className="text-xs px-2 py-0.5 rounded-full bg-muted">
            {creds?.status ?? 'not registered'}
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          {creds?.registered && !conn?.connected && (
            <button
              type="button"
              onClick={() => connect.mutate()}
              disabled={connect.isPending}
              className="inline-flex items-center gap-2 rounded-lg bg-brand-teal-500 px-4 py-2 text-sm font-medium text-brand-forest-950"
            >
              <ExternalLink className="h-4 w-4" />
              Connect Google Business Profile
            </button>
          )}
          {creds?.registered && (
            <button
              type="button"
              onClick={() => refresh.mutate()}
              disabled={refresh.isPending}
              className="inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm"
            >
              <RefreshCw className={`h-4 w-4 ${refresh.isPending ? 'animate-spin' : ''}`} />
              Refresh connection
            </button>
          )}
          {conn?.connected && (
            <>
              <button
                type="button"
                onClick={() => syncReviews.mutate()}
                disabled={syncReviews.isPending}
                className="inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm"
              >
                Sync reviews
              </button>
              <button
                type="button"
                onClick={() => disconnect.mutate()}
                className="inline-flex items-center gap-2 rounded-lg border border-red-500/40 px-4 py-2 text-sm text-red-600"
              >
                <Unplug className="h-4 w-4" />
                Disconnect
              </button>
            </>
          )}
        </div>
        {conn?.connected && (
          <p className="text-sm text-muted-foreground">
            Connected to {conn.location_title}. Last sync:{' '}
            {conn.last_sync_at ? new Date(conn.last_sync_at).toLocaleString('en-GB') : 'never'}
          </p>
        )}
        {locations.length > 1 && (
          <div className="flex flex-wrap gap-2 pt-2 border-t">
            <select
              value={pickLocation}
              onChange={(e) => setPickLocation(e.target.value)}
              className="rounded-lg border px-3 py-2 text-sm min-w-[240px]"
            >
              <option value="">Switch location…</option>
              {locations.map((loc) => (
                <option key={loc.name} value={loc.name}>
                  {loc.title || loc.name}
                </option>
              ))}
            </select>
            <button
              type="button"
              disabled={!pickLocation}
              onClick={() => selectLocation.mutate(pickLocation)}
              className="rounded-lg border px-4 py-2 text-sm"
            >
              Apply
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
