'use client'

import { useMemo } from 'react'
import { useParams } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import { publicBooking } from '@/lib/api-client'
import {
  extractBookingFormFromWidget,
  resolvePublicBookingSchema,
} from '@/lib/booking-form-defaults'
import { toast } from 'sonner'
import { PublicBookShell } from '@/components/bookings/PublicBookShell'
import { DynamicPublicBookingForm } from '@/components/bookings/DynamicPublicBookingForm'

type WidgetConfig = {
  tenant_slug?: string
  tenant_name?: string
  widget_primary_color?: string
  services?: { id: string; name: string; duration_minutes?: number; deposit_pence?: number }[]
  deposit_enabled?: boolean
  default_deposit_pence?: number
  error?: string
}

export default function PublicBookPage() {
  const { tenant_slug: slug } = useParams<{ tenant_slug: string }>()

  const {
    data: widget,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['public-booking-widget', slug],
    queryFn: async () => {
      const r = await publicBooking.widget(slug)
      const data = r.data as WidgetConfig
      if (data?.error === 'not_found' || !data?.tenant_slug) {
        throw new Error('This booking page is not available.')
      }
      return data
    },
    enabled: !!slug,
    retry: 1,
  })

  const bookMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      publicBooking.create(slug, payload).then((r) => r.data),
    onSuccess: (data: { message?: string; manage_url?: string; payment?: { client_secret?: string } }) => {
      toast.success(data.message || 'Booking confirmed')
      if (data.payment?.client_secret && data.manage_url) {
        toast.message('Deposit required', {
          description: 'Complete payment from your booking management link.',
        })
      }
      if (data.manage_url) window.location.href = data.manage_url
    },
    onError: (e: { response?: { data?: { detail?: string } }; message?: string }) =>
      toast.error(e.response?.data?.detail ?? e.message ?? 'Could not complete booking'),
  })

  const accent = widget?.widget_primary_color || '#166534'
  const schema = useMemo(
    () => resolvePublicBookingSchema(extractBookingFormFromWidget(widget as Record<string, unknown>)),
    [widget],
  )

  const errDetail =
    (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
    (error as Error | undefined)?.message

  if (isLoading) {
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

  if (isError || !widget) {
    return (
      <PublicBookShell
        variant="booking"
        tenantName="Booking unavailable"
        subtitle="This business page could not be loaded."
        accent={accent}
      >
        <p className="text-sm text-slate-600 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
          {errDetail ||
            'The business may be inactive or the link is incorrect. Contact the business directly.'}
        </p>
      </PublicBookShell>
    )
  }

  return (
    <PublicBookShell
      variant="booking"
      tenantName={widget.tenant_name || 'Book online'}
      subtitle="Complete the form below to request your appointment."
      accent={accent}
    >
      <DynamicPublicBookingForm
        slug={slug}
        schema={schema}
        services={widget.services ?? []}
        depositEnabled={widget.deposit_enabled}
        defaultDepositPence={widget.default_deposit_pence}
        accent={accent}
        onSubmit={(payload) => bookMutation.mutate(payload)}
        isPending={bookMutation.isPending}
      />
    </PublicBookShell>
  )
}
