'use client'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { bookings } from '@/lib/api-client'
import { useState } from 'react'
import { toast } from 'sonner'

export default function BookingWidgetPage() {
  const { data: linkData } = useQuery({
    queryKey: ['bookings', 'link'],
    queryFn: () => bookings.getLink().then((r) => r.data),
  })

  const [copied, setCopied] = useState(false)
  const bookUrl = linkData?.url || ''
  const slug = linkData?.slug || 'your-slug'
  const embedCode = `<script src="${typeof window !== 'undefined' ? window.location.origin : ''}/embed/booking-widget.js" data-tenant="${slug}" data-book-url="${bookUrl}"></script>`

  const copy = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    toast.success('Copied')
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center gap-3">
        <Link href="/dashboard/bookings" className="text-sm text-brand-teal-100/70 hover:text-white">← Bookings</Link>
        <h1 className="text-2xl font-bold text-foreground">Booking widget</h1>
      </div>
      <div className="rounded-xl border border-brand-forest-800 bg-brand-forest-950 p-6 space-y-4">
        <div>
          <p className="text-sm text-brand-teal-100/70 mb-1">Public booking link</p>
          <p className="text-white font-mono text-sm break-all">{bookUrl || '…'}</p>
          <button type="button" onClick={() => copy(bookUrl)} className="mt-2 text-xs text-brand-teal-300 hover:underline">
            {copied ? 'Copied!' : 'Copy link'}
          </button>
        </div>
        <div>
          <p className="text-sm text-brand-teal-100/70 mb-2">Embed on your website</p>
          <pre className="text-xs bg-brand-forest-900 p-4 rounded-lg overflow-x-auto text-brand-teal-100/90">{embedCode}</pre>
          <button type="button" onClick={() => copy(embedCode)} className="mt-2 text-xs text-brand-teal-300 hover:underline">Copy embed code</button>
        </div>
      </div>
    </div>
  )
}
