'use client'

import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'next/navigation'
import { ExternalLink, Link2, RefreshCw, Unplug } from 'lucide-react'
import { toast } from 'sonner'
import { integrations } from '@/lib/api-client'

interface GoogleStatus {
  connected: boolean
  configured: boolean
  location_title: string | null
  google_location_name: string | null
  last_sync_at: string | null
  available_locations: { name: string; title: string }[]
}

export default function IntegrationsPage() {
  const qc = useQueryClient()
  const searchParams = useSearchParams()
  const [pickLocation, setPickLocation] = useState('')

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
      toast.error('Google connection failed. Check test-user access and try again.')
    }
  }, [searchParams, qc])

  const disconnect = useMutation({
    mutationFn: () => integrations.googleDisconnect(),
    onSuccess: () => {
      toast.success('Google disconnected')
      qc.invalidateQueries({ queryKey: ['integrations', 'google'] })
    },
    onError: () => toast.error('Could not disconnect Google'),
  })

  const selectLocation = useMutation({
    mutationFn: (location_name: string) => integrations.googleSelectLocation(location_name),
    onSuccess: () => {
      toast.success('Location updated')
      qc.invalidateQueries({ queryKey: ['integrations', 'google'] })
    },
    onError: () => toast.error('Could not update location'),
  })

  const sync = useMutation({
    mutationFn: () => integrations.googleSync(),
    onSuccess: (res) => {
      toast.success(`Synced ${res.data.total_fetched} reviews from Google`)
      qc.invalidateQueries({ queryKey: ['integrations', 'google'] })
      qc.invalidateQueries({ queryKey: ['google-reviews'] })
    },
    onError: () => toast.error('Sync failed — reconnect Google if needed'),
  })

  const data = status.data
  const locations = data?.available_locations ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Integrations</h1>
        <p className="text-muted-foreground text-sm">
          Connect Google Business Profile to view and reply to reviews from your dashboard.
        </p>
      </div>

      <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-6 shadow-sm space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex gap-3">
            <div className="rounded-lg bg-brand-teal-400/10 p-2">
              <Link2 className="h-5 w-5 text-brand-teal-300" />
            </div>
            <div>
              <h2 className="font-semibold text-white">Google Business Profile</h2>
              <p className="text-sm text-brand-teal-100/70 mt-1">
                {data?.connected
                  ? `Connected — ${data.location_title ?? 'Location selected'}`
                  : data?.configured
                    ? 'Not connected — use a Google account listed as a test user in Google Cloud.'
                    : 'Not configured on this server (contact support).'}
              </p>
              {data?.last_sync_at && (
                <p className="text-xs text-brand-teal-100/50 mt-1">
                  Last sync: {new Date(data.last_sync_at).toLocaleString('en-GB')}
                </p>
              )}
            </div>
          </div>
          <span
            className={`text-xs px-2 py-0.5 rounded-full ${
              data?.connected
                ? 'bg-green-400/20 text-green-100 ring-1 ring-green-300/30'
                : 'bg-gray-400/20 text-gray-200 ring-1 ring-gray-300/30'
            }`}
          >
            {data?.connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          {!data?.connected && data?.configured && (
            <a
              href={integrations.googleConnectUrl()}
              className="inline-flex items-center gap-2 rounded-lg bg-brand-teal-500 px-4 py-2 text-sm font-medium text-brand-forest-950 hover:bg-brand-teal-400"
            >
              <ExternalLink className="h-4 w-4" />
              Connect Google
            </a>
          )}
          {data?.connected && (
            <>
              <button
                type="button"
                onClick={() => sync.mutate()}
                disabled={sync.isPending}
                className="inline-flex items-center gap-2 rounded-lg border border-brand-forest-600 px-4 py-2 text-sm text-white hover:bg-brand-forest-800 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${sync.isPending ? 'animate-spin' : ''}`} />
                Sync reviews
              </button>
              <button
                type="button"
                onClick={() => disconnect.mutate()}
                disabled={disconnect.isPending}
                className="inline-flex items-center gap-2 rounded-lg border border-red-500/40 px-4 py-2 text-sm text-red-200 hover:bg-red-950/40 disabled:opacity-50"
              >
                <Unplug className="h-4 w-4" />
                Disconnect
              </button>
            </>
          )}
        </div>

        {locations.length > 1 && (
          <div className="pt-4 border-t border-brand-forest-800 space-y-2">
            <p className="text-sm text-brand-teal-100/80">Switch business location</p>
            <div className="flex flex-wrap gap-2">
              <select
                value={pickLocation}
                onChange={(e) => setPickLocation(e.target.value)}
                className="rounded-lg border border-brand-forest-600 bg-brand-forest-900 px-3 py-2 text-sm text-white min-w-[240px]"
              >
                <option value="">Select location…</option>
                {locations.map((loc) => (
                  <option key={loc.name} value={loc.name}>
                    {loc.title || loc.name}
                  </option>
                ))}
              </select>
              <button
                type="button"
                disabled={!pickLocation || selectLocation.isPending}
                onClick={() => selectLocation.mutate(pickLocation)}
                className="rounded-lg bg-brand-teal-500/90 px-4 py-2 text-sm font-medium text-brand-forest-950 disabled:opacity-50"
              >
                Apply
              </button>
            </div>
          </div>
        )}
      </div>

      {data?.connected && (
        <p className="text-sm text-muted-foreground">
          Open{' '}
          <a href="/dashboard/reviews" className="text-brand-teal-400 hover:underline">
            Reviews
          </a>{' '}
          and use the Google tab to read and reply.
        </p>
      )}
    </div>
  )
}
