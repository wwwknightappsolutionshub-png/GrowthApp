'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { bookings, auth, tenants } from '@/lib/api-client'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import { Copy, ExternalLink, LayoutGrid, QrCode } from 'lucide-react'
import { BookingsPanel, BookingsSubpageLayout } from '@/components/bookings/BookingsSubpageLayout'

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
    queryFn: () => tenants.get().then((r) => r.data as { name?: string; is_active?: boolean }),
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
  const workspaceInactive = tenant?.is_active === false
  const needsPublicBookingFix = slugArchived || workspaceInactive
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
    <BookingsSubpageLayout
      tenantName={tenant?.name}
      userName={me?.full_name}
      subtitle="Widget embed & QR codes for booking, referrals, and feedback"
    >
      {needsPublicBookingFix ? (
        <div className="w-full rounded-xl border border-amber-500/40 bg-amber-950/40 px-4 py-3 text-sm text-amber-100 text-center">
          <p className="font-semibold text-amber-50 mb-1">
            {slugArchived ? 'Archived booking URL detected' : 'Public booking is disabled'}
          </p>
          <p className="text-amber-100/90 mb-3">
            {slugArchived ? (
              <>
                Public link may use an archived slug (<span className="font-mono text-xs">-deleted-…</span>).
                Fix below, then re-print QR codes.
              </>
            ) : (
              <>Workspace inactive — enable public booking below or reactivate in Super Admin.</>
            )}
          </p>
          <button
            type="button"
            onClick={() => restoreSlug.mutate()}
            disabled={restoreSlug.isPending}
            className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-sm font-semibold disabled:opacity-50"
          >
            {restoreSlug.isPending
              ? 'Enabling…'
              : slugArchived
                ? 'Restore clean booking URL'
                : 'Enable public booking'}
          </button>
        </div>
      ) : null}

      <BookingsPanel className="space-y-5">
        <h2 className="text-lg font-bold text-white flex items-center justify-center gap-2">
          <LayoutGrid className="w-5 h-5 text-brand-teal-300" />
          Website embed
        </h2>
        <div>
          <p className="text-sm text-brand-teal-100/70 mb-1 text-center">Public booking link</p>
          <p className="text-white font-mono text-sm break-all bg-brand-forest-900/80 rounded-lg px-3 py-2 border border-brand-forest-700">
            {bookUrl || '…'}
          </p>
          <div className="mt-2 flex justify-center">
            <button
              type="button"
              onClick={() => bookUrl && copy(bookUrl, 'link')}
              className="inline-flex items-center gap-1.5 text-xs text-brand-teal-300 hover:underline"
            >
              <Copy className="w-3.5 h-3.5" />
              {copied === 'link' ? 'Copied!' : 'Copy link'}
            </button>
          </div>
        </div>
        <div>
          <p className="text-sm text-brand-teal-100/70 mb-2 text-center">Embed snippet</p>
          <pre className="text-xs bg-brand-forest-900 p-4 rounded-lg overflow-x-auto text-brand-teal-100/90 border border-brand-forest-700 text-left">
            {embedCode}
          </pre>
          <div className="mt-2 flex justify-center">
            <button
              type="button"
              onClick={() => copy(embedCode, 'embed')}
              className="inline-flex items-center gap-1.5 text-xs text-brand-teal-300 hover:underline"
            >
              <Copy className="w-3.5 h-3.5" />
              {copied === 'embed' ? 'Copied!' : 'Copy embed code'}
            </button>
          </div>
        </div>
      </BookingsPanel>

      <BookingsPanel>
        <h2 className="text-lg font-bold text-white flex items-center justify-center gap-2 mb-1">
          <QrCode className="w-5 h-5 text-brand-teal-300" />
          Three QR use cases
        </h2>
        <p className="text-sm text-brand-teal-100/65 mb-6 text-center">
          Print or share — each code opens a distinct customer journey.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          {qrTargets.map((t) => (
            <div
              key={t.id}
              className="rounded-xl border border-brand-forest-700 bg-brand-forest-900 p-4 text-center flex flex-col"
            >
              <p className="text-sm font-semibold text-white mb-1">{t.label}</p>
              <p className="text-xs text-brand-teal-100/55 mb-3 min-h-[2.5rem] flex-1">{t.description}</p>
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
                  <p className="text-[10px] text-brand-teal-100/45 font-mono break-all line-clamp-2 px-1 w-full">
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
      </BookingsPanel>
    </BookingsSubpageLayout>
  )
}
