'use client'

import { useParams } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import { publicBooking } from '@/lib/api-client'
import { toast } from 'sonner'
import { PublicBookShell } from '@/components/bookings/PublicBookShell'
import { DynamicPublicBookingForm } from '@/components/bookings/DynamicPublicBookingForm'
import type { FormSchema } from '@/components/bookings/BookingFormBuilder'

export default function PublicBookPage() {
  const { tenant_slug: slug } = useParams<{ tenant_slug: string }>()

  const { data: widget } = useQuery({
    queryKey: ['public-booking-widget', slug],
    queryFn: () => publicBooking.widget(slug).then((r) => r.data),
    enabled: !!slug,
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
    onError: () => toast.error('Could not complete booking'),
  })

  const accent = widget?.widget_primary_color || '#166534'
  const schema = (widget?.booking_form || { version: 1, fields: [] }) as FormSchema

  return (
    <PublicBookShell
      tenantName={widget?.tenant_name || 'Book online'}
      subtitle="Complete the form below to request your appointment."
      accent={accent}
    >
      <DynamicPublicBookingForm
        slug={slug}
        schema={schema}
        services={widget?.services ?? []}
        depositEnabled={widget?.deposit_enabled}
        defaultDepositPence={widget?.default_deposit_pence}
        accent={accent}
        onSubmit={(payload) => bookMutation.mutate(payload)}
        isPending={bookMutation.isPending}
      />
    </PublicBookShell>
  )
}
