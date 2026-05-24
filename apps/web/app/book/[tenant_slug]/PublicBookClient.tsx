'use client'

import { useMemo, useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { CheckCircle2 } from 'lucide-react'
import { publicBooking } from '@/lib/api-client'
import {
  extractBookingFormFromWidget,
  resolvePublicBookingSchema,
} from '@/lib/booking-form-defaults'
import type { PublicWidgetLoadResult, PublicWidgetPayload } from '@/lib/public-booking-server'
import { toast } from 'sonner'
import { PublicBookShell } from '@/components/bookings/PublicBookShell'
import { DynamicPublicBookingForm } from '@/components/bookings/DynamicPublicBookingForm'

type Props = {
  slug: string
  initialWidget: PublicWidgetPayload | null
  loadStatus: PublicWidgetLoadResult['status']
}

function UnavailablePanel({ slug, detail }: { slug: string; detail: string }) {
  const deleted = slug.includes('deleted')
  return (
    <p className="text-sm text-slate-600 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 space-y-2">
      <span className="block">{detail}</span>
      {deleted ? (
        <span className="block text-amber-900/90">
          This link uses a <strong>deleted</strong> business slug. In your dashboard, open{' '}
          <strong>Bookings → Widget &amp; QR codes</strong> and use the active booking URL or QR
          code shown there.
        </span>
      ) : null}
    </p>
  )
}

export function PublicBookClient({ slug, initialWidget, loadStatus }: Props) {
  const [confirmed, setConfirmed] = useState<{
    message: string
    manageUrl?: string
    rewardsPortalUrl?: string
    loyaltyWalletMessage?: string
  } | null>(null)

  const {
    data: widget,
    isPending,
    isError,
    error,
    isFetched,
  } = useQuery({
    queryKey: ['public-booking-widget', slug],
    queryFn: async () => {
      const r = await publicBooking.widget(slug)
      const data = r.data as PublicWidgetPayload
      if (data?.error === 'not_found' || (!data?.tenant_slug && !data?.tenant_name)) {
        throw new Error('This booking page is not available.')
      }
      return data
    },
    initialData: loadStatus === 'ok' && initialWidget ? initialWidget : undefined,
    enabled: !!slug,
    retry: 1,
    staleTime: 30_000,
    refetchOnMount: true,
  })

  const bookMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      publicBooking.create(slug, payload).then((r) => r.data),
    onSuccess: (data: {
      message?: string
      manage_url?: string
      payment?: { client_secret?: string }
      rewards_portal_url?: string
      loyalty_wallet_message?: string
    }) => {
      const message = data.message || 'Booking confirmed! We will be in touch shortly.'
      if (data.payment?.client_secret && data.manage_url) {
        toast.success(message)
        toast.message('Deposit required', {
          description: 'Complete payment from your booking management link.',
        })
        window.location.href = data.manage_url
        return
      }
      toast.success(message)
      setConfirmed({
        message,
        manageUrl: data.manage_url,
        rewardsPortalUrl: data.rewards_portal_url,
        loyaltyWalletMessage: data.loyalty_wallet_message,
      })
    },
    onError: (e: { response?: { data?: { detail?: string } }; message?: string }) =>
      toast.error(e.response?.data?.detail ?? e.message ?? 'Could not complete booking'),
  })

  const active = widget ?? (loadStatus === 'ok' ? initialWidget : null)
  const accent = active?.widget_primary_color || '#166534'
  const schema = useMemo(
    () => resolvePublicBookingSchema(extractBookingFormFromWidget(active as Record<string, unknown>)),
    [active],
  )

  const errDetail =
    (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
    (error as Error | undefined)?.message

  const showLoading = (isPending || (!isFetched && !active)) && !isError

  if ((isError || (isFetched && !active)) && !showLoading) {
    const inactiveHint =
      loadStatus === 'not_found' && !slug.includes('deleted')
        ? 'The booking URL looks correct, but this workspace may still be archived. In Super Admin, open Tenants → Reactivate, or in Bookings → Widget use “Restore clean booking URL”.'
        : 'This business is inactive or the booking link is outdated.'
    return (
      <PublicBookShell
        variant="booking"
        tenantName="Booking unavailable"
        subtitle="This business is not accepting online bookings."
        accent={accent}
      >
        <UnavailablePanel slug={slug} detail={errDetail || inactiveHint} />
      </PublicBookShell>
    )
  }

  if (showLoading) {
    return (
      <PublicBookShell variant="booking" tenantName="Loading…" subtitle="Preparing your booking form…" accent={accent}>
        <div className="space-y-3 animate-pulse">
          <div className="h-10 bg-slate-100 rounded-lg" />
          <div className="h-10 bg-slate-100 rounded-lg" />
          <div className="h-10 bg-slate-100 rounded-lg" />
          <div className="h-24 bg-slate-100 rounded-lg" />
        </div>
      </PublicBookShell>
    )
  }

  if (confirmed) {
    return (
      <PublicBookShell
        variant="booking"
        tenantName={active?.tenant_name || 'Book online'}
        subtitle="Your appointment request has been received."
        accent={accent}
      >
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-5 py-6 text-center space-y-3">
          <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto" aria-hidden />
          <p className="text-emerald-900 font-semibold">{confirmed.message}</p>
          <p className="text-sm text-emerald-800/80">
            We&apos;ll confirm your appointment by email or phone shortly.
          </p>
          {confirmed.manageUrl ? (
            <a
              href={confirmed.manageUrl}
              className="inline-block text-sm text-emerald-700 underline hover:text-emerald-900 mt-2"
            >
              Need to reschedule or cancel later?
            </a>
          ) : null}
          {confirmed.rewardsPortalUrl ? (
            <div className="mt-4 rounded-lg border border-emerald-300/60 bg-white/70 px-4 py-3 text-left space-y-2">
              <p className="text-sm font-medium text-emerald-900">Your rewards wallet</p>
              <p className="text-sm text-emerald-800/90">
                {confirmed.loyaltyWalletMessage ??
                  'Track points, redeem rewards, and show your in-store QR from your personal wallet.'}
              </p>
              <a
                href={confirmed.rewardsPortalUrl}
                className="inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-semibold text-white"
                style={{ backgroundColor: accent }}
              >
                Open rewards wallet
              </a>
            </div>
          ) : null}
        </div>
      </PublicBookShell>
    )
  }

  return (
    <PublicBookShell
      variant="booking"
      tenantName={active?.tenant_name || 'Book online'}
      subtitle="Complete the form below to request your appointment."
      accent={accent}
    >
      <DynamicPublicBookingForm
        slug={slug}
        schema={schema}
        services={active?.services ?? []}
        depositEnabled={active?.deposit_enabled}
        defaultDepositPence={active?.default_deposit_pence}
        loyaltyProgramAvailable={active?.loyalty_program_available}
        loyaltyProgramLabel={active?.loyalty_program_label}
        accent={accent}
        onSubmit={(payload) => bookMutation.mutate(payload)}
        isPending={bookMutation.isPending}
      />
    </PublicBookShell>
  )
}
