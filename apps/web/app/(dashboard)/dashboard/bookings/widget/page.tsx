'use client'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { bookings } from '@/lib/api-client'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import { Copy, LayoutGrid, QrCode } from 'lucide-react'

function qrImageUrl(data: string, size = 220) {
  return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(data)}`
}

export default function BookingWidgetPage() {
  const { data: linkData } = useQuery({
    queryKey: ['bookings', 'link'],
    queryFn: () => bookings.getLink().then((r) => r.data),
  })

  const [copied, setCopied] = useState<'link' | 'embed' | null>(null)
  const bookUrl = linkData?.url || ''
  const slug = linkData?.slug || 'your-slug'
  const origin = typeof window !== 'undefined' ? window.location.origin : ''
  const embedCode = `<script src="${origin}/embed/booking-widget.js" data-tenant="${slug}" data-book-url="${bookUrl}"></script>`

  const qrTargets = useMemo(
    () => [
      { id: 'booking', label: 'Public booking page', value: bookUrl },
      { id: 'widget', label: 'Widget landing', value: bookUrl ? `${bookUrl}?embed=1` : '' },
      { id: 'manage', label: 'Manage booking (token link pattern)', value: `${origin}/book/manage` },
    ],
    [bookUrl, origin],
  )

  const copy = (text: string, kind: 'link' | 'embed') => {
    navigator.clipboard.writeText(text)
    setCopied(kind)
    toast.success('Copied')
    setTimeout(() => setCopied(null), 2000)
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-3">
        <Link href="/dashboard/bookings" className="text-sm text-brand-teal-100/70 hover:text-white">
          ← Bookings
        </Link>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <LayoutGrid className="w-6 h-6 text-brand-teal-300" />
          Booking widget & QR codes
        </h1>
      </div>

      <div className="rounded-2xl border border-brand-forest-800 bg-brand-forest-950 p-6 space-y-4">
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
          <p className="text-sm text-brand-teal-100/70 mb-2">Embed on your website</p>
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
          Centralized QR codes
        </h2>
        <p className="text-sm text-brand-teal-100/65 mb-6">
          Print or share these codes — customers scan to book without typing a URL.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {qrTargets.map((t) => (
            <div
              key={t.id}
              className="rounded-xl border border-brand-forest-700 bg-brand-forest-900 p-4 text-center"
            >
              <p className="text-sm font-semibold text-white mb-3">{t.label}</p>
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
                  Loading link…
                </div>
              )}
              {t.value ? (
                <button
                  type="button"
                  onClick={() => copy(t.value, 'link')}
                  className="mt-3 text-xs text-brand-teal-300 hover:underline"
                >
                  Copy URL
                </button>
              ) : null}
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
