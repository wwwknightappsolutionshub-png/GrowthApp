'use client'

import Link from 'next/link'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { bookings, auth, tenants } from '@/lib/api-client'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import { Copy, ExternalLink, LayoutGrid, Pencil, QrCode } from 'lucide-react'
import { TenantWelcomeHeader } from '@/components/dashboard/TenantWelcomeHeader'

function qrImageUrl(data: string, size = 220) {
  return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(data)}`
}

export default function BookingWidgetPage() {
  const qc = useQueryClient()
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
    queryFn: () =>
      bookings.getLinks().then(
        (r) =>
          r.data as {
            slug?: string
            booking_url?: string
            slug_archived?: boolean
            refer_label?: string
            booking_label?: string
            review_label?: string
            referral_url?: string
            rate_url?: string
          },
      ),
  })

  const restoreSlug = useMutation({
    mutationFn: () => bookings.restoreBookingSlug().then((r) => r.data),
    onSuccess: () => {
      toast.success('Booking URL restored — re-print your QR codes')
      qc.invalidateQueries({ queryKey: ['bookings', 'links'] })
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? 'Could not restore URL'),
  })

  const [copied, setCopied] = useState<string | null>(null)
  const bookUrl = links?.booking_url || ''
  const slug = links?.slug || 'your-slug'
  const slugArchived = links?.slug_archived || slug.includes('-deleted-')
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
          className="inline-flex items-center gap-1.5 text-sm text-brand-teal-300 hover:text-white font-medium"
        >
          <Pencil className="w-3.5 h-3.5" />
          Booking form builder (QR A)
        </Link>
      </div>

      {slugArchived ? (
        <div className="rounded-xl border border-amber-500/40 bg-amber-950/40 px-4 py-3 text-sm text-amber-100">
          <p className="font-semibold text-amber-50 mb-1">Archived booking URL detected</p>
          <p className="text-amber-100/90 mb-3">
            This workspace was previously deleted, so the public link still uses an archived slug (
            <span className="font-mono text-xs">-deleted-…</span>). Customer QR codes will not work until
            you restore a clean URL.
          </p>
          <button
            type="button"
            onClick={() => restoreSlug.mutate()}
            disabled={restoreSlug.isPending}
            className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-sm font-semibold disabled:opacity-50"
          >
            {restoreSlug.isPending ? 'Restoring…' : 'Restore clean booking URL'}
          </button>
        </div>
      ) : null}

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
                <div className="mt-3 flex flex-col items-center gap-2">
                  <p className="text-[10px] text-brand-teal-100/45 font-mono break-all line-clamp-2 px-1">
                    {t.value}
                  </p>
                  <a
                    href={t.value}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-white bg-brand-forest-700 hover:bg-brand-forest-600 px-3 py-1.5 rounded-lg"
                  >
                    <ExternalLink className="w-3 h-3" />
                    Open preview
                  </a>
                  <button
                    type="button"
                    onClick={() => copy(t.value, t.id)}
                    className="text-xs text-brand-teal-300 hover:underline"
                  >
                    {copied === t.id ? 'Copied!' : 'Copy URL'}
                  </button>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
