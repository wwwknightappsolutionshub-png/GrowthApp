'use client'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { bookings, auth, tenants } from '@/lib/api-client'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import { Copy, LayoutGrid, QrCode } from 'lucide-react'
import { TenantWelcomeHeader } from '@/components/dashboard/TenantWelcomeHeader'

function qrImageUrl(data: string, size = 220) {
  return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(data)}`
}

export default function BookingWidgetPage() {
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
    queryFn: () => bookings.getLinks().then((r) => r.data),
  })

  const [copied, setCopied] = useState<string | null>(null)
  const bookUrl = links?.booking_url || ''
  const slug = links?.slug || 'your-slug'
  const origin = typeof window !== 'undefined' ? window.location.origin : ''
  const embedCode = `<script src="${origin}/embed/booking-widget.js" data-tenant="${slug}" data-book-url="${bookUrl}"></script>`

  const qrTargets = useMemo(
    () => [
      {
        id: 'booking',
        label: links?.booking_label ?? 'Public booking page',
        description: 'Form builder — book appointment',
        value: links?.booking_url ?? '',
      },
      {
        id: 'referral',
        label: links?.refer_label ?? 'Refer & Win',
        description: 'Referral form → CRM pipeline (New)',
        value: links?.referral_url ?? '',
      },
      {
        id: 'rate',
        label: links?.review_label ?? 'Review & Comments',
        description: 'Opens Google review (GMB connected)',
        value: links?.rate_url ?? '',
      },
    ],
    [links],
  )

  const copy = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopied(id)
    toast.success('Copied')
    setTimeout(() => setCopied(null), 2000)
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <TenantWelcomeHeader
        tenantName={tenant?.name}
        userName={me?.full_name}
        subtitle="Widget embed & QR codes for booking, referrals, and feedback"
      />
      <div className="flex flex-wrap items-center gap-3">
        <Link href="/dashboard/bookings" className="text-sm text-brand-teal-100/70 hover:text-white">
          ← Bookings hub
        </Link>
        <Link
          href="/dashboard/bookings/form-builder"
          className="text-sm text-brand-teal-300 hover:text-white font-medium"
        >
          Edit booking form (QR A) →
        </Link>
      </div>

      <div className="rounded-2xl border border-brand-forest-800 bg-brand-forest-950 p-6 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <LayoutGrid className="w-5 h-5 text-brand-teal-300" />
          Website embed
        </h2>
        <div>
          <p className="text-sm text-brand-teal-100/70 mb-1">Public booking link</p>
          <p className="text-white font-mono text-sm break-all">{bookUrl || '…'}</p>
          <button
            type="button"
            onClick={() => bookUrl && copy(bookUrl, 'link')}
            className="mt-2 inline-flex items-center gap-1.5 text-xs text-brand-teal-300 hover:underline"
          >
            <Copy className="w-3.5 h-3.5" />
            {copied === 'link' ? 'Copied!' : 'Copy link'}
          </button>
        </div>
        <div>
          <p className="text-sm text-brand-teal-100/70 mb-2">Embed snippet</p>
          <pre className="text-xs bg-brand-forest-900 p-4 rounded-lg overflow-x-auto text-brand-teal-100/90">
            {embedCode}
          </pre>
          <button
            type="button"
            onClick={() => copy(embedCode, 'embed')}
            className="mt-2 inline-flex items-center gap-1.5 text-xs text-brand-teal-300 hover:underline"
          >
            <Copy className="w-3.5 h-3.5" />
            {copied === 'embed' ? 'Copied!' : 'Copy embed code'}
          </button>
        </div>
      </div>

      <section className="rounded-2xl border border-brand-forest-800 bg-brand-forest-950 p-6">
        <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-1">
          <QrCode className="w-5 h-5 text-brand-teal-300" />
          Three QR use cases
        </h2>
        <p className="text-sm text-brand-teal-100/65 mb-6">
          Print or share — each code opens a distinct customer journey aligned with your operations.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {qrTargets.map((t) => (
            <div
              key={t.id}
              className="rounded-xl border border-brand-forest-700 bg-brand-forest-900 p-4 text-center"
            >
              <p className="text-sm font-semibold text-white mb-1">{t.label}</p>
              <p className="text-xs text-brand-teal-100/55 mb-3 min-h-[2.5rem]">{t.description}</p>
              {t.value ? (
                <img
                  src={qrImageUrl(t.value)}
                  alt={`QR code for ${t.label}`}
                  width={200}
                  height={200}
                  className="mx-auto rounded-lg bg-white p-2"
                />
              ) : (
                <div className="h-[200px] flex items-center justify-center text-xs text-brand-teal-100/50">
                  Loading…
                </div>
              )}
              {t.value ? (
                <button
                  type="button"
                  onClick={() => copy(t.value, t.id)}
                  className="mt-3 text-xs text-brand-teal-300 hover:underline"
                >
                  {copied === t.id ? 'Copied!' : 'Copy URL'}
                </button>
              ) : null}
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
