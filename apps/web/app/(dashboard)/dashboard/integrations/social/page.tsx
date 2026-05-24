'use client'

import Link from 'next/link'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Copy, Link2 } from 'lucide-react'
import { toast } from 'sonner'
import { integrations } from '@/lib/api-client'

const PLATFORMS = [
  { id: 'facebook', label: 'Facebook' },
  { id: 'instagram', label: 'Instagram' },
  { id: 'tiktok', label: 'TikTok' },
  { id: 'linkedin', label: 'LinkedIn' },
] as const

interface SocialChannel {
  id: string
  channel_type: string
  webhook_url: string
  api_key: string
  zapier_integration_key: string | null
  make_integration_key: string | null
  status: string
  connected_at: string | null
}

function copyText(text: string, label: string) {
  navigator.clipboard.writeText(text).then(
    () => toast.success(`${label} copied`),
    () => toast.error('Copy failed'),
  )
}

export default function SocialIntegrationsPage() {
  const qc = useQueryClient()
  const channels = useQuery<SocialChannel[]>({
    queryKey: ['integrations', 'social', 'channels'],
    queryFn: () => integrations.socialChannels().then((r) => r.data),
  })

  const provision = useMutation({
    mutationFn: (platform: string) => integrations.provisionSocialChannel(platform),
    onSuccess: () => {
      toast.success('Channel provisioned')
      qc.invalidateQueries({ queryKey: ['integrations', 'social'] })
    },
    onError: () => toast.error('Could not provision channel'),
  })

  const byPlatform = Object.fromEntries((channels.data ?? []).map((c) => [c.channel_type, c]))

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
        <h1 className="text-2xl font-bold text-foreground">Social Connections</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Connect Facebook, Instagram, TikTok and LinkedIn via Zapier or Make. CustomerFlow receives
          webhooks into your unified inbox.
        </p>
      </div>

      <div className="rounded-xl border bg-muted/40 p-4 text-sm space-y-2">
        <p className="font-medium">Zapier / Make setup</p>
        <ol className="list-decimal list-inside text-muted-foreground space-y-1">
          <li>Click Connect for each platform below.</li>
          <li>Copy the Webhook URL into a Zapier Catch Hook or Make Custom Webhook module.</li>
          <li>Map fields: event_type, platform, sender_name, message, sender_email, sender_phone.</li>
          <li>Send a test payload — status changes to connected when received.</li>
        </ol>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {PLATFORMS.map(({ id, label }) => {
          const ch = byPlatform[id]
          return (
            <div key={id} className="rounded-xl border bg-card p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Link2 className="h-4 w-4 text-brand-teal-600" />
                  <h2 className="font-semibold">{label}</h2>
                </div>
                <span className="text-xs px-2 py-0.5 rounded-full bg-muted">{ch?.status ?? 'not set up'}</span>
              </div>

              {!ch ? (
                <button
                  type="button"
                  onClick={() => provision.mutate(id)}
                  disabled={provision.isPending}
                  className="rounded-lg bg-brand-forest-700 px-4 py-2 text-sm font-medium text-white"
                >
                  Connect {label} via Zapier
                </button>
              ) : (
                <div className="space-y-2 text-xs">
                  {[
                    ['Webhook URL', ch.webhook_url],
                    ['API Key', ch.api_key],
                    ['Zapier key', ch.zapier_integration_key ?? '—'],
                    ['Make key', ch.make_integration_key ?? '—'],
                  ].map(([labelText, value]) => (
                    <div key={labelText} className="flex items-center gap-2">
                      <span className="text-muted-foreground w-24 shrink-0">{labelText}</span>
                      <code className="flex-1 truncate rounded bg-muted px-2 py-1">{value}</code>
                      <button
                        type="button"
                        onClick={() => copyText(String(value), labelText)}
                        className="p-1 rounded hover:bg-muted"
                        aria-label={`Copy ${labelText}`}
                      >
                        <Copy className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
