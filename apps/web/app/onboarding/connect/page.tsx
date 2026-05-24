'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight, Link2, SkipForward } from 'lucide-react'
import { toast } from 'sonner'
import { integrations } from '@/lib/api-client'

export default function OnboardingConnectPage() {
  const router = useRouter()
  const qc = useQueryClient()

  const save = useMutation({
    mutationFn: (data: { google_connected?: boolean; social_connected?: boolean; skipped?: boolean }) =>
      integrations.saveIntegrationsOnboarding(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['integrations', 'onboarding'] })
      router.push('/onboarding')
    },
    onError: () => toast.error('Could not save progress'),
  })

  const google = useQuery({
    queryKey: ['integrations', 'google', 'credentials'],
    queryFn: () => integrations.googleCredentials().then((r) => r.data),
  })

  const social = useQuery({
    queryKey: ['integrations', 'social', 'channels'],
    queryFn: () => integrations.socialChannels().then((r) => r.data),
  })

  const googleReady = google.data?.status === 'connected'
  const socialReady = (social.data ?? []).some((c: { status: string }) => c.status === 'connected')

  return (
    <div className="mx-auto max-w-2xl space-y-8 pb-24">
      <div className="text-center">
        <h1 className="text-2xl font-bold">Connect your platforms</h1>
        <p className="text-sm text-muted-foreground mt-2">
          Optional — connect Google and social channels now, or skip and set up later in Settings.
        </p>
      </div>

      <div className="grid gap-4">
        <Link
          href="/dashboard/integrations/google"
          className="flex items-center gap-4 rounded-xl border p-5 hover:bg-muted/50"
        >
          <Link2 className="h-6 w-6 text-brand-teal-600" />
          <div className="flex-1">
            <p className="font-semibold">Google Business Profile</p>
            <p className="text-sm text-muted-foreground">Use your own Google Cloud OAuth app</p>
          </div>
          <span className="text-xs rounded-full px-2 py-0.5 bg-muted">
            {googleReady ? 'Connected' : 'Not connected'}
          </span>
        </Link>

        <Link
          href="/dashboard/integrations/social"
          className="flex items-center gap-4 rounded-xl border p-5 hover:bg-muted/50"
        >
          <Link2 className="h-6 w-6 text-brand-teal-600" />
          <div className="flex-1">
            <p className="font-semibold">Social via Zapier / Make</p>
            <p className="text-sm text-muted-foreground">Facebook, Instagram, TikTok, LinkedIn</p>
          </div>
          <span className="text-xs rounded-full px-2 py-0.5 bg-muted">
            {socialReady ? 'Connected' : 'Not connected'}
          </span>
        </Link>
      </div>

      <div className="flex flex-wrap gap-3 justify-center">
        <button
          type="button"
          onClick={() =>
            save.mutate({
              google_connected: googleReady,
              social_connected: socialReady,
              skipped: false,
            })
          }
          disabled={save.isPending}
          className="inline-flex items-center gap-2 rounded-md bg-brand-forest-700 px-5 py-2 text-sm font-semibold text-white"
        >
          Continue
          <ArrowRight className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={() => save.mutate({ skipped: true })}
          disabled={save.isPending}
          className="inline-flex items-center gap-2 rounded-md border px-5 py-2 text-sm"
        >
          <SkipForward className="h-4 w-4" />
          Skip for now
        </button>
      </div>
    </div>
  )
}
