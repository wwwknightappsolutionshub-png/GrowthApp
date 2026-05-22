'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { LayoutGrid } from 'lucide-react'
import { bookings, auth, tenants } from '@/lib/api-client'
import { TenantWelcomeHeader } from '@/components/dashboard/TenantWelcomeHeader'
import { BookingFormBuilder, type FormSchema } from '@/components/bookings/BookingFormBuilder'
import {
  DEFAULT_PUBLIC_BOOKING_SCHEMA,
  schemaFromFormApi,
} from '@/lib/booking-form-defaults'

export default function TenantBookingFormBuilderPage() {
  const qc = useQueryClient()
  const [schema, setSchema] = useState<FormSchema>(DEFAULT_PUBLIC_BOOKING_SCHEMA)

  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: () => auth.me().then((r) => r.data as { full_name?: string }),
  })
  const { data: tenant } = useQuery({
    queryKey: ['tenant'],
    queryFn: () => tenants.get().then((r) => r.data as { name?: string }),
  })

  const { data: links } = useQuery({
    queryKey: ['bookings', 'links'],
    queryFn: () => bookings.getLinks().then((r) => r.data as { booking_url?: string; slug?: string }),
  })

  const { data: formData, isLoading } = useQuery({
    queryKey: ['bookings', 'form'],
    queryFn: () => bookings.getForm().then((r) => r.data),
  })

  useEffect(() => {
    if (isLoading) return
    const loaded = schemaFromFormApi(formData as Record<string, unknown> | undefined)
    if (loaded) setSchema(loaded)
  }, [formData, isLoading])

  const save = useMutation({
    mutationFn: () => {
      if (!schema.fields?.length) {
        return Promise.reject(new Error('Form must include at least one field'))
      }
      return bookings.updateForm({ schema })
    },
    onSuccess: () => {
      toast.success('Booking form saved')
      qc.invalidateQueries({ queryKey: ['bookings', 'form'] })
      qc.invalidateQueries({ queryKey: ['bookings', 'links'] })
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? 'Save failed'),
  })

  return (
    <div className="space-y-6 max-w-3xl">
      <TenantWelcomeHeader
        tenantName={tenant?.name}
        userName={me?.full_name}
        subtitle="Customise your public booking form (QR A)"
      />
      <Link href="/dashboard/bookings/widget" className="text-sm text-brand-teal-100/70 hover:text-white">
        ← Widget & QR codes
      </Link>

      <div className="rounded-2xl border border-brand-forest-800 bg-brand-forest-950 p-6">
        <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-1">
          <LayoutGrid className="w-5 h-5 text-brand-teal-300" />
          Form builder
        </h2>
        <p className="text-xs text-brand-teal-100/60 mb-4">
          Category: <span className="text-brand-teal-200">{formData?.category ?? '…'}</span>
          {formData?.is_tenant_override ? ' · customised' : ' · using platform default'}
        </p>
        {isLoading ? (
          <p className="text-sm text-brand-teal-100/60">Loading…</p>
        ) : (
          <>
            <p className="text-xs text-brand-teal-100/55 mb-3">
              {schema.fields.length} field(s). Edit labels and types; add custom questions with{' '}
              <strong className="text-brand-teal-200">Add field</strong>. Service/slot types stay
              fixed so appointments work.
            </p>
            <BookingFormBuilder schema={schema} onChange={setSchema} />
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => save.mutate()}
                disabled={save.isPending || !schema.fields?.length}
                className="px-4 py-2 rounded-lg bg-brand-teal-600 text-white text-sm font-semibold disabled:opacity-50"
              >
                {save.isPending ? 'Saving…' : 'Save booking form'}
              </button>
              {links?.booking_url ? (
                <a
                  href={links.booking_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-brand-teal-300 hover:text-white underline"
                >
                  Preview public form →
                </a>
              ) : null}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
